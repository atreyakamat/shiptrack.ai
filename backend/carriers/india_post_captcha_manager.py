"""
In-app CAPTCHA relay for India Post tracking.

The user still solves the CAPTCHA themselves — this never auto-solves or bypasses it.
It simply runs the India Post page in a headless browser, hands the CAPTCHA *image*
to the ShipTrack UI, takes the human's answer back, types it into the same live
session and presses TRACK. The challenge India Post set is answered by a person on
every lookup; only the surface the person sees it on has changed.

All Playwright calls run on one dedicated worker thread (Playwright's sync API is
single-threaded), driven by a command queue, so Flask request threads never touch
the browser directly.
"""
import logging
import queue
import secrets
import threading
import time
from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Tuple

from .india_post_web import IndiaPostWebAdapter, INDIA_POST_URL

logger = logging.getLogger(__name__)

SESSION_TTL_SEC = 180          # abandon a session after 3 minutes
RESULT_WAIT_SEC = 25           # how long to wait for a result after TRACK is pressed
MAX_CONCURRENT_SESSIONS = 8    # cap simultaneous live browser tabs


@dataclass
class _Session:
    context: Any
    page: Any
    tracking_number: str
    user_id: int
    created_at: float = field(default_factory=time.time)


class _Command:
    __slots__ = ("name", "args", "reply")

    def __init__(self, name: str, args: tuple):
        self.name = name
        self.args = args
        self.reply: "queue.Queue" = queue.Queue(maxsize=1)


class IndiaPostCaptchaManager:
    """Singleton that owns a headless browser and relays CAPTCHAs to the UI."""

    _instance: Optional["IndiaPostCaptchaManager"] = None
    _instance_lock = threading.Lock()

    def __init__(self):
        self._commands: "queue.Queue[_Command]" = queue.Queue()
        self._sessions: Dict[str, _Session] = {}
        self._adapter = IndiaPostWebAdapter()
        self._started = threading.Event()
        self._worker = threading.Thread(target=self._run, name="india-post-captcha", daemon=True)
        self._worker.start()
        self._started.wait(timeout=30)

    @classmethod
    def instance(cls) -> "IndiaPostCaptchaManager":
        with cls._instance_lock:
            if cls._instance is None:
                cls._instance = IndiaPostCaptchaManager()
            return cls._instance

    # ---- public API (called from Flask request threads) ---------------------------

    def start_session(self, tracking_number: str, user_id: int) -> Dict[str, Any]:
        """Open the page, fill the number, return a session id + the CAPTCHA image."""
        return self._dispatch("open", (tracking_number.strip().upper(), user_id))

    def submit_answer(self, session_id: str, answer: str, user_id: int) -> Dict[str, Any]:
        """Submit the human's CAPTCHA answer; returns a tracking result, a retry, or an error."""
        return self._dispatch("submit", (session_id, answer.strip(), user_id))

    def cancel(self, session_id: str, user_id: int) -> None:
        self._dispatch("cancel", (session_id, user_id))

    # ---- command plumbing ---------------------------------------------------------

    def _dispatch(self, name: str, args: tuple) -> Any:
        cmd = _Command(name, args)
        self._commands.put(cmd)
        ok, payload = cmd.reply.get()
        if not ok:
            raise payload
        return payload

    def _run(self):
        from playwright.sync_api import sync_playwright
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
                self._started.set()
                while True:
                    try:
                        cmd = self._commands.get(timeout=30)
                    except queue.Empty:
                        self._reap(browser)
                        continue
                    try:
                        result = self._handle(browser, cmd.name, cmd.args)
                        cmd.reply.put((True, result))
                    except Exception as e:  # never let the worker die on one bad command
                        logger.error(f"captcha manager command {cmd.name} failed: {e}")
                        cmd.reply.put((False, e))
                    self._reap(browser)
        except Exception as e:
            logger.error(f"captcha manager worker crashed: {e}")
            self._started.set()

    def _handle(self, browser, name: str, args: tuple):
        if name == "open":
            return self._open(browser, *args)
        if name == "submit":
            return self._submit(*args)
        if name == "cancel":
            return self._close(args[0], args[1])
        raise ValueError(f"unknown command {name}")

    # ---- command implementations (worker thread only) -----------------------------

    def _open(self, browser, tracking_number: str, user_id: int) -> Dict[str, Any]:
        if not self._adapter.validate_tracking_number(tracking_number):
            raise ValueError("Invalid India Post tracking number format.")
        if len(self._sessions) >= MAX_CONCURRENT_SESSIONS:
            raise RuntimeError("Too many tracking sessions in progress. Please try again shortly.")

        context = browser.new_context(viewport={"width": 1366, "height": 800})
        page = context.new_page()
        page.set_default_timeout(45000)
        try:
            page.goto(INDIA_POST_URL, wait_until="load", timeout=60000)
        except Exception as e:
            logger.warning(f"India Post nav slow: {e}")
        page.wait_for_timeout(2500)
        self._dismiss_language(page)

        track_input = self._find_tracking_input(page)
        if not track_input:
            context.close()
            raise RuntimeError("Could not find the India Post tracking field; the site may have changed.")
        self._type_and_verify(page, track_input, tracking_number)

        captcha = self._read_captcha(page)
        if not captcha:
            context.close()
            raise RuntimeError("Could not read the CAPTCHA image from India Post.")

        session_id = secrets.token_urlsafe(18)
        self._sessions[session_id] = _Session(context, page, tracking_number, user_id)
        return {"session_id": session_id, "captcha_image": captcha, "tracking_number": tracking_number}

    def _submit(self, session_id: str, answer: str, user_id: int) -> Dict[str, Any]:
        session = self._sessions.get(session_id)
        if not session or session.user_id != user_id:
            raise LookupError("This tracking session has expired. Please start again.")
        if not answer:
            raise ValueError("Please enter the CAPTCHA text.")

        page = session.page
        cap_in = page.locator("input[placeholder*='captcha' i]").first
        cap_in.fill("")
        cap_in.fill(answer)
        track_btn = page.locator("button:has-text('TRACK'), button:has-text('Track')").first
        track_btn.click()

        deadline = time.time() + RESULT_WAIT_SEC
        while time.time() < deadline:
            page.wait_for_timeout(1000)
            try:
                result = self._adapter.extract_table_data(page.content(), session.tracking_number)
            except Exception:
                result = {"events": []}
            if result.get("events"):
                self._close(session_id, user_id)
                return {"status": "success", "data": result}
            if self._page_says_not_found(page):
                self._close(session_id, user_id)
                return {"status": "not_found",
                        "message": "India Post has no records for this number yet."}

        # No result: most likely a wrong/expired CAPTCHA. Hand back a fresh image to retry.
        fresh = self._read_captcha(page)
        if fresh:
            return {"status": "captcha_failed", "captcha_image": fresh,
                    "message": "That CAPTCHA didn't go through. Please try the new image."}
        self._close(session_id, user_id)
        raise TimeoutError("No result and no new CAPTCHA appeared. Please start again.")

    # ---- helpers ------------------------------------------------------------------

    def _dismiss_language(self, page):
        for sel in ["button[lang='en']", "button[aria-label*='English' i]"]:
            try:
                loc = page.locator(sel).first
                if loc.count() and loc.is_visible():
                    loc.click(timeout=5000)
                    page.wait_for_timeout(600)
                    return
            except Exception:
                pass

    def _find_tracking_input(self, page):
        for _ in range(20):
            for sel in ["#hero-track-input", "input[placeholder*='Consignment' i]",
                        "input[placeholder*='Money Order' i]"]:
                loc = page.locator(sel).first
                try:
                    if loc.count() and loc.is_visible():
                        return loc
                except Exception:
                    pass
            page.wait_for_timeout(1000)
        return None

    def _type_and_verify(self, page, track_input, tracking_number: str):
        for _ in range(8):
            try:
                track_input.click()
                track_input.fill("")
                track_input.press_sequentially(tracking_number, delay=35)
                page.wait_for_timeout(500)
                if (track_input.input_value() or "").strip().upper() == tracking_number:
                    return
            except Exception:
                page.wait_for_timeout(400)

    def _read_captcha(self, page) -> Optional[str]:
        cap = page.locator("img[alt*='captcha' i], img[src*='captcha' i]").first
        for _ in range(10):
            try:
                if cap.count():
                    src = cap.get_attribute("src") or ""
                    if src.startswith("data:image"):
                        return src
            except Exception:
                pass
            page.wait_for_timeout(500)
        return None

    def _page_says_not_found(self, page) -> bool:
        try:
            txt = page.inner_text("body").lower()
        except Exception:
            return False
        return any(s in txt for s in ["no record", "not found", "no data found", "invalid consignment"])

    def _close(self, session_id: str, user_id: int):
        session = self._sessions.pop(session_id, None)
        if session:
            try:
                session.context.close()
            except Exception:
                pass

    def _reap(self, browser):
        now = time.time()
        for sid in [s for s, v in self._sessions.items() if now - v.created_at > SESSION_TTL_SEC]:
            logger.info(f"captcha session {sid} expired; closing")
            self._close(sid, self._sessions[sid].user_id if sid in self._sessions else -1)
