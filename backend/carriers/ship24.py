"""
Ship24 adapter — authorized aggregator API for live tracking (no CAPTCHA).

Ship24's free tier allows a limited number of active trackers. ShipTrack uses Ship24
for up to that many shipments; once a shipment is marked done we release its tracker to
free a slot (the data is already saved in our DB). Beyond the quota, the app falls back
to the in-app CAPTCHA relay.
"""
import logging
import os
import time
from typing import Any, Dict, List, Optional

import requests

from .base import BaseCarrierAdapter
from .normalizer import CarrierNormalizer

logger = logging.getLogger(__name__)

BASE_URL = "https://api.ship24.com/public/v1"

# Ship24 statusMilestone -> ShipTrack canonical status.
MILESTONE_MAP = {
    "pending": BaseCarrierAdapter.STATUS_BOOKED,
    "info_received": BaseCarrierAdapter.STATUS_BOOKED,
    "in_transit": BaseCarrierAdapter.STATUS_IN_TRANSIT,
    "out_for_delivery": BaseCarrierAdapter.STATUS_OUT_FOR_DELIVERY,
    "available_for_pickup": BaseCarrierAdapter.STATUS_ARRIVED_AT_FACILITY,
    "failed_attempt": BaseCarrierAdapter.STATUS_EXCEPTION,
    "exception": BaseCarrierAdapter.STATUS_EXCEPTION,
    "delivered": BaseCarrierAdapter.STATUS_DELIVERED,
}


class Ship24Adapter(BaseCarrierAdapter):
    def __init__(self, api_key: Optional[str] = None, timeout: int = 20):
        self.api_key = api_key or os.getenv("TRACKING_API_KEY", "")
        self.timeout = timeout

    # ---- auth / http --------------------------------------------------------------

    def _headers(self) -> Dict[str, str]:
        if not self.api_key:
            raise ValueError("Ship24 tracking requires TRACKING_API_KEY to be set.")
        return {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}

    def validate_tracking_number(self, tracking_number: str) -> bool:
        return bool(tracking_number and tracking_number.strip())

    def normalize_status(self, raw_status: str) -> str:
        return CarrierNormalizer.normalize_status(raw_status)

    def get_latest_location(self, events: List[Dict[str, Any]]) -> Optional[str]:
        # Events are stored earliest-first, so the current location is the newest event's.
        for event in reversed(events):
            loc = event.get('location')
            if loc and str(loc).strip() and str(loc).strip().lower() != 'unknown':
                return str(loc).strip()
        return None

    # ---- quota management ---------------------------------------------------------

    def active_tracker_count(self) -> int:
        """How many trackers currently exist on the account (the free-tier quota unit)."""
        try:
            res = requests.get(f"{BASE_URL}/trackers?page=1", headers=self._headers(), timeout=self.timeout)
            res.raise_for_status()
            return len(res.json().get("data", {}).get("trackers", []))
        except requests.RequestException as e:
            logger.warning(f"Ship24 tracker count failed: {e}")
            raise ConnectionError(f"Could not reach Ship24: {e}")

    def find_tracker_id(self, tracking_number: str) -> Optional[str]:
        tracking_number = tracking_number.strip().upper()
        try:
            res = requests.get(f"{BASE_URL}/trackers?page=1", headers=self._headers(), timeout=self.timeout)
            res.raise_for_status()
            for t in res.json().get("data", {}).get("trackers", []):
                if (t.get("trackingNumber") or "").strip().upper() == tracking_number:
                    return t.get("trackerId")
            return None
        except requests.RequestException as e:
            logger.warning(f"Ship24 tracker lookup failed: {e}")
            return None

    def delete_tracker(self, tracker_id: str) -> bool:
        """Attempt to release a tracker. NOTE: Ship24's public API does not expose a
        DELETE for trackers (returns 404 'Cannot DELETE'), so this currently cannot free
        a quota slot programmatically. Kept for if/when Ship24 adds it; callers must treat
        a False return as 'slot not freed'."""
        try:
            res = requests.delete(f"{BASE_URL}/trackers/{tracker_id}", headers=self._headers(), timeout=self.timeout)
            if res.status_code in (200, 204):
                return True
            logger.info(f"Ship24 delete tracker not supported (HTTP {res.status_code}).")
            return False
        except requests.RequestException as e:
            logger.warning(f"Ship24 delete tracker failed: {e}")
            return False

    # ---- tracking -----------------------------------------------------------------

    def track(self, tracking_number: str) -> Dict[str, Any]:
        tracking_number = tracking_number.strip().upper()
        res = None
        last_err = None
        # Retry transient failures (timeouts, connection errors, 5xx) a couple of times.
        for attempt in range(3):
            try:
                res = requests.post(f"{BASE_URL}/trackers/track", headers=self._headers(),
                                    json={"trackingNumber": tracking_number}, timeout=self.timeout)
                if res.status_code < 500:
                    break
                last_err = f"HTTP {res.status_code}"
            except requests.Timeout:
                last_err = "timeout"
            except requests.RequestException as e:
                last_err = str(e)
            if attempt < 2:
                time.sleep(0.5 * (attempt + 1))
        if res is None:
            if last_err == "timeout":
                raise TimeoutError("Ship24 timed out. Please try again.")
            raise ConnectionError(f"Could not reach Ship24: {last_err}")

        if res.status_code in (401, 403):
            raise PermissionError("Ship24 authentication failed. Check TRACKING_API_KEY.")
        if res.status_code == 402 or res.status_code == 429:
            raise RuntimeError("Ship24 quota or rate limit reached.")
        if res.status_code >= 500:
            raise ConnectionError(f"Ship24 is unavailable (HTTP {res.status_code}).")
        res.raise_for_status()

        trackings = (res.json().get("data") or {}).get("trackings") or []
        if not trackings:
            return {"details": {"tracking_number": tracking_number, "status": self.STATUS_UNKNOWN,
                                "origin": None, "destination": None, "article_type": None}, "events": []}
        return self._normalize(tracking_number, trackings[0])

    def get_tracking_history(self, tracking_number: str) -> List[Dict[str, Any]]:
        return self.track(tracking_number).get("events", [])

    # ---- normalisation ------------------------------------------------------------

    def _normalize(self, tracking_number: str, tracking: Dict[str, Any]) -> Dict[str, Any]:
        raw_events = tracking.get("events") or []
        events = []
        for e in raw_events:
            when = e.get("occurrenceDatetime") or e.get("datetime") or ""
            iso_date, _, time = when.partition("T")
            time = time.replace("Z", "").split(".")[0] or None
            # Store dates as DD/MM/YYYY to match the India Post web adapter, so events
            # dedup correctly when a shipment is tracked by both Ship24 and the CAPTCHA relay.
            date = iso_date
            parts = iso_date.split("-")
            if len(parts) == 3:
                date = f"{parts[2]}/{parts[1]}/{parts[0]}"
            status = e.get("status") or "Status Updated"
            location = e.get("location")
            events.append({
                "date": date or None,
                "time": time,
                "location": location,
                "status": status,
                "raw_status": status,
                "normalized_status": self._event_status(e),
                "description": status,
            })

        # Ship24 returns newest-first; our pipeline treats earliest-first, so reverse.
        events.reverse()

        milestone = (tracking.get("shipment", {}) or {}).get("statusMilestone")
        # Prefer the latest event's text (handles India Post phrasing like "on hold"),
        # falling back to Ship24's milestone.
        overall = None
        if events:
            overall = CarrierNormalizer.normalize_status(events[-1]["raw_status"])
        if not overall or overall == self.STATUS_UNKNOWN:
            overall = MILESTONE_MAP.get(milestone, self.STATUS_UNKNOWN)

        origin = events[0]["location"] if events else None
        details = {
            "tracking_number": tracking_number,
            "status": overall,
            "origin": origin,
            "destination": None,
            "article_type": None,
            "tracker_id": (tracking.get("tracker") or {}).get("trackerId"),
        }
        return {"details": details, "events": events}

    def _event_status(self, event: Dict[str, Any]) -> str:
        text = event.get("status") or ""
        mapped = CarrierNormalizer.normalize_status(text)
        if mapped != self.STATUS_UNKNOWN:
            return mapped
        return MILESTONE_MAP.get(event.get("statusMilestone"), self.STATUS_UNKNOWN)
