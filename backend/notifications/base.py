from abc import ABC, abstractmethod
from typing import Dict, Any

class BaseNotificationProvider(ABC):
    """
    Abstract base class for all notification providers.
    """
    @abstractmethod
    def send(self, event_type: str, shipment_id: int, message: str, context: Dict[str, Any] = None) -> bool:
        """
        Send a notification.
        
        :param event_type: The type of event (e.g. 'OUT_FOR_DELIVERY')
        :param shipment_id: The ID of the shipment, if applicable
        :param message: The text message to send
        :param context: Additional structured context (e.g. tracking number, location)
        :return: True if successful, False otherwise
        """
        pass
