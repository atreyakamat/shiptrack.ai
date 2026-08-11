from typing import List, Dict, Any
from .base import BaseCarrierAdapter
import re

class IndiaPostAdapter(BaseCarrierAdapter):
    def track(self, tracking_number: str) -> Dict[str, Any]:
        if not self.validate_tracking_number(tracking_number):
            raise ValueError(f"Invalid India Post tracking number: {tracking_number}")
        # Explicit block as per requirements. No CAPTCHA bypassing.
        raise NotImplementedError('Live India Post tracking requires an authorized tracking integration.')

    def get_tracking_history(self, tracking_number: str) -> List[Dict[str, Any]]:
        raise NotImplementedError('Live India Post tracking requires an authorized tracking integration.')

    def validate_tracking_number(self, tracking_number: str) -> bool:
        return bool(re.match(r'^[A-Z]{2}[0-9]{9}IN$', tracking_number))

    def normalize_status(self, raw_status: str) -> str:
        s = raw_status.lower()
        if 'delivered' in s or 'delivery confirmed' in s: return self.STATUS_DELIVERED
        if 'out for delivery' in s: return self.STATUS_OUT_FOR_DELIVERY
        if 'booked' in s: return self.STATUS_BOOKED
        if 'dispatched' in s: return self.STATUS_DISPATCHED
        if 'arrived' in s: return self.STATUS_ARRIVED_AT_FACILITY
        if 'received' in s or 'bagged' in s: return self.STATUS_IN_TRANSIT
        if 'delay' in s: return self.STATUS_DELAYED
        if 'return' in s: return self.STATUS_RETURNED
        return self.STATUS_UNKNOWN
