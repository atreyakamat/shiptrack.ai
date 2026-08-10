from typing import List, Dict, Any
from .base import BaseCarrierAdapter
import re

class IndiaPostAdapter(BaseCarrierAdapter):
    def track(self, tracking_number: str) -> Dict[str, Any]:
        if not self.validate_tracking_number(tracking_number):
            raise ValueError(f"Invalid India Post tracking number: {tracking_number}")
        # Connect to India Post, but CAPTCHA stops us
        raise Exception('Live India Post tracking is not currently configured due to CAPTCHA restrictions.')

    def get_tracking_history(self, tracking_number: str) -> List[Dict[str, Any]]:
        raise Exception('Live India Post tracking is not currently configured due to CAPTCHA restrictions.')

    def validate_tracking_number(self, tracking_number: str) -> bool:
        return bool(re.match(r'^[A-Z]{2}[0-9]{9}IN$', tracking_number))

    def normalize_status(self, raw_status: str) -> str:
        s = raw_status.lower()
        if 'delivered' in s or 'delivery confirmed' in s: return self.STATUS_DELIVERED
        if 'out for delivery' in s: return self.STATUS_OUT_FOR_DELIVERY
        if 'booked' in s: return self.STATUS_BOOKED
        if 'dispatched' in s: return self.STATUS_DISPATCHED
        if 'received' in s or 'bagged' in s: return self.STATUS_IN_TRANSIT
        return self.STATUS_UNKNOWN
