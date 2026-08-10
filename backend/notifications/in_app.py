import logging
from typing import Dict, Any
from .base import BaseNotificationProvider
from backend.models.notification import Notification
from backend.extensions import db
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

class InAppNotificationProvider(BaseNotificationProvider):
    def send(self, event_type: str, shipment_id: int, message: str, context: Dict[str, Any] = None) -> bool:
        try:
            from backend.models.shipment import Shipment
            shipment = Shipment.query.get(shipment_id)
            if not shipment:
                return False
                
            notif = Notification(
                user_id=shipment.user_id,
                shipment_id=shipment_id,
                notification_type=event_type,
                message=message,
                channel='in_app',
                sent_at=datetime.now(timezone.utc)
            )
            db.session.add(notif)
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to create in-app notification: {e}")
            return False
