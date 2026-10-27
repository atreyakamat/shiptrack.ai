"""
Human-Assisted India Post Web Tracking Adapter for ShipTrack AI.
Uses Playwright to open the official India Post tracking page in an interactive browser,
pre-fills the tracking number, allows the user to solve the CAPTCHA,
and automatically extracts the tracking results into ShipTrack's canonical event schema.
"""
import os
import re
import json
import time
import logging
from typing import Dict, Any, List, Optional
from bs4 import BeautifulSoup
from .base import BaseCarrierAdapter
from .normalizer import CarrierNormalizer

logger = logging.getLogger(__name__)

INDIA_POST_URL = "https://www.indiapost.gov.in/"

class IndiaPostWebAdapter(BaseCarrierAdapter):
    def __init__(self, headless: Optional[bool] = None, timeout_sec: int = 90):
        if headless is None:
            self.headless = os.getenv('PLAYWRIGHT_HEADLESS', 'false').lower() == 'true'
        else:
            self.headless = headless
        self.timeout_sec = int(os.getenv('PLAYWRIGHT_TIMEOUT_SEC', str(timeout_sec)))

    def validate_tracking_number(self, tracking_number: str) -> bool:
        if not tracking_number:
            return False
        return bool(re.match(r'^[A-Z]{2}[0-9]{9}[A-Z]{2}$', tracking_number.strip().upper()))

    def normalize_status(self, raw_status: str) -> str:
        return CarrierNormalizer.normalize_status(raw_status)

    def get_latest_location(self, events: List[Dict[str, Any]]) -> Optional[str]:
        # This adapter returns events in chronological (earliest-first) order, so the
        # current location is the newest event's, i.e. the last one with a real location.
        for event in reversed(events):
            loc = event.get('location')
            if loc and str(loc).strip() and str(loc).strip().lower() != 'unknown':
                return str(loc).strip()
        return None

    # India Post renders real values on <canvas> and keeps the true text only in the
    # aria-label of the wrapping role="img" span. Hidden <span data-fake>XX..YY</span>
    # decoys are injected to poison naive text scraping. _real_text reads the aria-labels
    # and drops the decoys; it never solves or defeats the CAPTCHA itself.
    DECOY_RE = re.compile(r'XX[0-9A-Za-z×]+?YY')

    @classmethod
    def _real_text(cls, el) -> str:
        if el is None:
            return ""
        nodes = []
        if el.get("role") == "img" and el.get("aria-label"):
            nodes.append(el)
        nodes.extend(el.find_all(attrs={"role": "img"}))
        labels = [n.get("aria-label", "").strip() for n in nodes if n.get("aria-label", "").strip()]
        if labels:
            return " ".join(labels).strip()
        # Fallback: strip decoy tokens from raw text if the page served plain values.
        return cls.DECOY_RE.sub('', el.get_text(" ", strip=True)).strip()

    def _summary_field(self, soup, label: str) -> Optional[str]:
        """Find a 'Label:' node and return the nearest real value near it."""
        node = soup.find(string=re.compile(re.escape(label)))
        container = node.parent if node else None
        for _ in range(4):
            if container is None:
                break
            img = container.find(attrs={"role": "img"})
            if img and img.get("aria-label"):
                return img.get("aria-label").strip()
            container = container.parent
        return None

    def extract_table_data(self, html_content: str, tracking_number: str) -> Dict[str, Any]:
        """Extracts structured events and summary details from the tracking results HTML."""
        soup = BeautifulSoup(html_content, "html.parser")
        events = []
        details = {
            "tracking_number": tracking_number,
            "status": BaseCarrierAdapter.STATUS_UNKNOWN,
            "origin": None,
            "destination": None,
            "article_type": None,
        }

        for table in soup.find_all("table"):
            rows = table.find_all("tr")
            if not rows:
                continue
            header_cells = [self._real_text(c).lower() for c in rows[0].find_all(["th", "td"])]
            header = " ".join(header_cells)
            if not any(k in header for k in ["event", "date", "time", "office", "status"]):
                continue

            # Map columns by header, so we are robust to column order across layouts.
            col = {"status": None, "date": None, "time": None, "office": None, "remarks": None}
            for i, h in enumerate(header_cells):
                if col["status"] is None and ("event" in h or "status" in h):
                    col["status"] = i
                elif col["date"] is None and "date" in h:
                    col["date"] = i
                elif col["time"] is None and "time" in h:
                    col["time"] = i
                elif col["office"] is None and ("office" in h or "location" in h):
                    col["office"] = i
                elif col["remarks"] is None and "remark" in h:
                    col["remarks"] = i

            def pick(cells, key):
                i = col[key]
                return cells[i] if i is not None and i < len(cells) else None

            for row in rows[1:]:
                cells = [self._real_text(td) for td in row.find_all(["td", "th"])]
                if len(cells) < 3:
                    continue
                ev_status = pick(cells, "status")
                ev_date = pick(cells, "date")
                ev_time = pick(cells, "time")
                ev_loc = pick(cells, "office")
                remarks = pick(cells, "remarks")
                if not ev_status or not ev_date:
                    continue
                if ev_loc and ev_loc.lower() in ["null", "none", "-", ""]:
                    ev_loc = None
                if remarks and remarks.strip() in ["-", ""]:
                    remarks = None
                events.append({
                    "date": ev_date,
                    "time": ev_time or None,
                    "location": ev_loc,
                    "status": ev_status,
                    "raw_status": ev_status,
                    "description": remarks or (f"{ev_status} at {ev_loc}" if ev_loc else ev_status),
                })

        # Summary fields (best-effort; None when absent).
        details["origin"] = self._summary_field(soup, "Booked At:")
        details["destination"] = self._summary_field(soup, "Destination:")
        details["article_type"] = self._summary_field(soup, "Article Type:")
        origin_pin = self._summary_field(soup, "Origin Pincode:")
        dest_pin = self._summary_field(soup, "Destination Pincode:")

        # Fallback: older layout keeps summary in a table (Booked At | Booked On | ... | Article Type).
        if not details["origin"] or not details["article_type"]:
            for table in soup.find_all("table"):
                rows = table.find_all("tr")
                if len(rows) < 2:
                    continue
                header_cells = [self._real_text(c).lower() for c in rows[0].find_all(["th", "td"])]
                if not any(k in " ".join(header_cells) for k in ["booked at", "destination pincode", "article type", "tariff"]):
                    continue
                cells = [self._real_text(td) for td in rows[1].find_all(["td", "th"])]

                def by_header(keyword, default_idx=None):
                    for i, h in enumerate(header_cells):
                        if keyword in h and i < len(cells):
                            return cells[i]
                    return cells[default_idx] if default_idx is not None and default_idx < len(cells) else None

                details["origin"] = details["origin"] or by_header("booked at", 0)
                details["article_type"] = details["article_type"] or by_header("article type")
                break
        details["article_type"] = details["article_type"] or "Speed Post"
        if events:
            details["origin"] = details["origin"] or events[0].get("location")
            details["destination"] = details["destination"] or events[-1].get("location")
            details["status"] = CarrierNormalizer.normalize_status(events[-1].get("raw_status"))

        raw_payload = {
            "data": {
                **details,
                "origin_pincode": origin_pin,
                "destination_pincode": dest_pin,
                "events": events,
            }
        }
        return CarrierNormalizer.normalize_response(tracking_number, raw_payload)

    DEBUG_CAPTURE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'logs', 'india_post_last_response.json')

    def _save_capture(self, captures: List[Dict[str, Any]]) -> None:
        """Persist raw responses so the parser can be tuned against India Post's real format."""
        try:
            os.makedirs(os.path.dirname(self.DEBUG_CAPTURE_PATH), exist_ok=True)
            with open(self.DEBUG_CAPTURE_PATH, 'w') as f:
                json.dump(captures, f, indent=2, default=str)
        except OSError as e:
            logger.warning(f"Could not write India Post debug capture: {e}")

    def _parse_captures(self, tracking_number: str, captures: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Return the first capture that normalizes to at least one event."""
        for cap in reversed(captures):
            body = cap.get('body')
            if not isinstance(body, (dict, list)):
                continue
            try:
                result = CarrierNormalizer.normalize_response(tracking_number, body if isinstance(body, dict) else {'data': body})
            except Exception as e:
                logger.debug(f"Capture from {cap.get('url')} did not normalize: {e}")
                continue
            if result.get('events'):
                return result
        return None

    def track(self, tracking_number: str) -> Dict[str, Any]:
        """
        Opens the official India Post page in a visible browser with the tracking number
        pre-filled. The USER solves the CAPTCHA and presses TRACK; this adapter never
        solves or bypasses it. The result is read from the page's own tracking response
        (falling back to the rendered page).
        """
        from playwright.sync_api import sync_playwright

        tracking_number = tracking_number.strip().upper()
        if not self.validate_tracking_number(tracking_number):
            raise ValueError(f"Invalid India Post tracking number format: {tracking_number}")

        logger.info(f"India Post human-assisted lookup for {tracking_number}: waiting up to {self.timeout_sec}s for CAPTCHA")
        captures: List[Dict[str, Any]] = []

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=self.headless, args=["--no-sandbox"])
            try:
                page = browser.new_context(viewport={"width": 1366, "height": 800}).new_page()

                def on_response(resp):
                    try:
                        if 'indiapost.gov.in' not in resp.url or resp.request.resource_type not in ('xhr', 'fetch'):
                            return
                        if not re.search(r'track|consign|article|booking', resp.url, re.I):
                            return
                        if 'json' not in (resp.headers.get('content-type') or ''):
                            return
                        captures.append({'url': resp.url, 'status': resp.status, 'body': resp.json()})
                    except Exception as e:  # response bodies can be unavailable (redirects, aborted)
                        logger.debug(f"Skipping response {resp.url}: {e}")

                page.on("response", on_response)
                page.set_default_timeout(60000)
                try:
                    page.goto(INDIA_POST_URL, timeout=60000, wait_until="load")
                except Exception as nav_err:
                    logger.warning(f"India Post nav slow, continuing: {nav_err}")
                # The site is a Next.js SPA; give it time to hydrate before touching inputs,
                # otherwise React resets whatever we type.
                page.wait_for_timeout(3000)

                # Dismiss the language chooser if shown.
                for sel in ["button[lang='en']", "button[aria-label*='English' i]"]:
                    try:
                        loc = page.locator(sel).first
                        if loc.count() and loc.is_visible():
                            loc.click(timeout=5000)
                            page.wait_for_timeout(800)
                            break
                    except Exception:
                        pass

                # Find the tracking input, retrying while the SPA finishes rendering.
                track_input = None
                for _ in range(20):
                    for sel in ["#hero-track-input", "input[placeholder*='Consignment' i]", "input[placeholder*='Money Order' i]"]:
                        loc = page.locator(sel).first
                        try:
                            if loc.count() and loc.is_visible():
                                track_input = loc
                                break
                        except Exception:
                            pass
                    if track_input:
                        break
                    page.wait_for_timeout(2000)
                if not track_input:
                    raise RuntimeError("Could not find the India Post tracking input. The site layout may have changed.")

                # Fill and VERIFY it stuck: type real keystrokes (React honours these) and
                # confirm the value survived re-render. Retry if hydration wiped it.
                filled = False
                for _ in range(8):
                    try:
                        track_input.click()
                        track_input.fill("")
                        track_input.press_sequentially(tracking_number, delay=40)
                        page.wait_for_timeout(700)
                        if (track_input.input_value() or "").strip().upper() == tracking_number:
                            filled = True
                            break
                    except Exception as fe:
                        logger.debug(f"Fill attempt failed, retrying: {fe}")
                        page.wait_for_timeout(600)
                if not filled:
                    logger.warning("Could not confirm the tracking number stuck; the user may need to type it manually.")

                try:
                    page.locator("input[placeholder*='captcha' i]").first.focus()
                except Exception:
                    pass
                logger.info(f"Tracking number {'filled' if filled else 'NOT confirmed'}. Waiting for the user to solve the CAPTCHA and press TRACK.")

                deadline = time.time() + self.timeout_sec
                while time.time() < deadline:
                    try:
                        page.wait_for_timeout(1000)
                        result = self._parse_captures(tracking_number, captures)
                        if not result:
                            dom = self.extract_table_data(page.content(), tracking_number)
                            result = dom if dom.get('events') else None
                    except Exception as e:
                        if "closed" in str(e).lower():
                            raise ConnectionError("The India Post window was closed before a result appeared. Please try Refresh again and solve the CAPTCHA.")
                        raise
                    if result:
                        self._save_capture(captures)
                        logger.info(f"Extracted {len(result['events'])} India Post events for {tracking_number}")
                        return result

                self._save_capture(captures)
                raise TimeoutError("No tracking result appeared. The CAPTCHA may not have been submitted, or the format is unrecognised.")
            finally:
                browser.close()

    def get_tracking_history(self, tracking_number: str) -> List[Dict[str, Any]]:
        data = self.track(tracking_number)
        return data.get("events", [])
