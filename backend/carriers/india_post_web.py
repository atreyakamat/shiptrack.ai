"""
Human-Assisted India Post Web Tracking Adapter for ShipTrack AI.
Uses Playwright to open the official India Post tracking page in an interactive browser,
pre-fills the tracking number, allows the user to solve the CAPTCHA,
and automatically extracts the tracking results into ShipTrack's canonical event schema.
"""
import os
import re
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

    def extract_table_data(self, html_content: str, tracking_number: str) -> Dict[str, Any]:
        """Extracts structured events and summary details from the tracking results HTML."""
        soup = BeautifulSoup(html_content, "html.parser")
        events = []
        details = {
            "tracking_number": tracking_number,
            "status": BaseCarrierAdapter.STATUS_UNKNOWN,
            "origin": None,
            "destination": None,
            "article_type": "Speed Post"
        }

        # Find all data tables on the page
        tables = soup.find_all("table")
        for table in tables:
            rows = table.find_all("tr")
            if not rows:
                continue

            # Check header to determine table type
            header_text = " ".join([th.get_text().strip().lower() for th in rows[0].find_all(["th", "td"])])
            
            # Event History Table (Date, Time, Office/Location, Event)
            if any(k in header_text for k in ["date", "time", "office", "event", "status"]):
                for row in rows[1:]:
                    cols = [td.get_text().strip() for td in row.find_all("td")]
                    if len(cols) >= 3:
                        # Typical order: Date | Time | Office | Event
                        if len(cols) >= 4:
                            ev_date, ev_time, ev_loc, ev_status = cols[0], cols[1], cols[2], cols[3]
                        elif len(cols) == 3:
                            ev_date, ev_loc, ev_status = cols[0], cols[1], cols[2]
                            ev_time = None
                        else:
                            continue

                        events.append({
                            "date": ev_date,
                            "time": ev_time,
                            "location": ev_loc if ev_loc and ev_loc.lower() not in ["null", "none"] else None,
                            "status": ev_status,
                            "raw_status": ev_status,
                            "description": f"{ev_status} at {ev_loc}" if ev_loc else ev_status
                        })

            # Summary Table (Booked At, Destination, Delivery Status)
            if any(k in header_text for k in ["booked at", "destination", "article type", "tariff"]):
                for row in rows[1:]:
                    cols = [td.get_text().strip() for td in row.find_all("td")]
                    if len(cols) >= 2:
                        details["origin"] = cols[0] if len(cols) > 0 else details["origin"]
                        details["destination"] = cols[2] if len(cols) > 2 else details["destination"]

        if events:
            # Check if any event indicates delivery, otherwise use the latest event
            delivered_ev = next((e for e in events if "deliver" in (e.get("raw_status") or "").lower()), None)
            if delivered_ev:
                details["status"] = BaseCarrierAdapter.STATUS_DELIVERED
            else:
                details["status"] = CarrierNormalizer.normalize_status(events[-1].get("raw_status") or events[0].get("raw_status"))
        
        raw_payload = {
            "data": {
                **details,
                "events": events
            }
        }
        return CarrierNormalizer.normalize_response(tracking_number, raw_payload)

    def track(self, tracking_number: str) -> Dict[str, Any]:
        """
        Launches Playwright in interactive mode, pre-fills the tracking number,
        prompts the user to solve the on-screen CAPTCHA, and parses the result.
        """
        from playwright.sync_api import sync_playwright
        
        tracking_number = tracking_number.strip().upper()
        if not self.validate_tracking_number(tracking_number):
            raise ValueError(f"Invalid India Post tracking number format: {tracking_number}")

        print("\n" + "="*60)
        print("INDIAPOST WEB TRACKING (HUMAN-ASSISTED)")
        print(f"Tracking Number: {tracking_number}")
        print("A browser window will open. Please enter the visible CAPTCHA and click 'Track Now'.")
        print("="*60 + "\n")

        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=self.headless,
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--no-sandbox",
                    "--disable-infobars"
                ]
            )
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
                viewport={"width": 1366, "height": 768}
            )
            page = context.new_page()
            page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

            try:
                page.goto(INDIA_POST_URL, timeout=30000, wait_until="load")
                page.wait_for_timeout(2000)

                # Locate and fill the consignment number input
                track_input = page.locator("input[placeholder*='Consignment' i], input[id*='txtTrkNo' i]").first
                if track_input.count() > 0:
                    track_input.fill(tracking_number)
                    print(f"[+] Entered tracking number {tracking_number} into form.")
                else:
                    raise RuntimeError("Could not find the Consignment Number input field on the India Post page.")

                # Focus on the CAPTCHA input for user convenience
                captcha_input = page.locator("#captcha-input, input[name*='captcha' i]").first
                if captcha_input.count() > 0:
                    captcha_input.focus()
                    print("[*] Focused on CAPTCHA input. Please enter the CAPTCHA and submit...")

                # Wait for results table or navigation after user solves CAPTCHA
                # Look for result tables or success container
                page.wait_for_selector(
                    "table, div.table-responsive, div#trackingResult, div.resultContainer",
                    timeout=self.timeout_sec * 1000
                )
                page.wait_for_timeout(2000) # Settle DOM

                html_content = page.content()
                result = self.extract_table_data(html_content, tracking_number)

                if not result.get("events"):
                    raise ValueError("No tracking event records found on the result page.")

                print(f"[+] Successfully extracted {len(result['events'])} tracking events.")
                return result

            except Exception as e:
                logger.error(f"Error during human-assisted tracking: {e}")
                raise ConnectionError(f"Human-assisted tracking failed or timed out: {e}")
            finally:
                browser.close()

    def get_tracking_history(self, tracking_number: str) -> List[Dict[str, Any]]:
        data = self.track(tracking_number)
        return data.get("events", [])
