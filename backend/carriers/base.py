from abc import ABC, abstractmethod
from typing import List, Dict, Any

class BaseCarrierAdapter(ABC):
    STATUS_BOOKED = 'BOOKED'
    STATUS_DISPATCHED = 'DISPATCHED'
    STATUS_IN_TRANSIT = 'IN_TRANSIT'
    STATUS_ARRIVED_AT_FACILITY = 'ARRIVED_AT_FACILITY'
    STATUS_OUT_FOR_DELIVERY = 'OUT_FOR_DELIVERY'
    STATUS_DELIVERED = 'DELIVERED'
    STATUS_DELAYED = 'DELAYED'
    STATUS_RETURNED = 'RETURNED'
    STATUS_EXCEPTION = 'EXCEPTION'
    STATUS_UNKNOWN = 'UNKNOWN'

    @abstractmethod
    def track(self, tracking_number: str) -> Dict[str, Any]:
        pass

    @abstractmethod
    def get_tracking_history(self, tracking_number: str) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def validate_tracking_number(self, tracking_number: str) -> bool:
        pass

    @abstractmethod
    def normalize_status(self, raw_status: str) -> str:
        pass

    def get_latest_location(self, events: List[Dict[str, Any]]) -> str:
        """
        Returns the latest known location from a list of tracking events.
        Events are assumed to be sorted latest-first, or we just find the newest one with a valid location.
        """
        for event in events:
            location = event.get('location')
            if location and str(location).strip() and str(location).strip().lower() != 'unknown':
                return str(location).strip()
        return "Unknown"
