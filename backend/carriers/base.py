from abc import ABC, abstractmethod
from typing import List, Dict, Any

class BaseCarrierAdapter(ABC):
    STATUS_BOOKED = 'BOOKED'
    STATUS_DISPATCHED = 'DISPATCHED'
    STATUS_IN_TRANSIT = 'IN_TRANSIT'
    STATUS_OUT_FOR_DELIVERY = 'OUT_FOR_DELIVERY'
    STATUS_DELIVERED = 'DELIVERED'
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
