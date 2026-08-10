import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from backend.extensions import db
from backend.models.notification import Notification
from backend.models.notification_preference import NotificationPreference

from backend.notifications import InAppNotificationProvider, WhatsAppNotificationProvider, EmailNotificationProvider

logger = logging.getLogger(__name__)

class NotificationService:
    @staticmethod
    def get_providers():
        return {
            'in_app': InAppNotificationProvider(),
            'whatsapp': WhatsAppNotificationProvider(),
            'email': EmailNotificationProvider()
        }

    @staticmethod
    def trigger_event(event_type: str, shipment_id: int, message: str, context: Dict[str, Any] = None) -> None:
        """
        Orchestrates notifications for an event. Looks up user preferences and dispatches to enabled providers.
        """
        try:
            from backend.models.shipment import Shipment
            shipment = Shipment.query.get(shipment_id)
            if not shipment:
                logger.warning(f"Shipment {shipment_id} not found for event {event_type}")
                return
                
            pref = NotificationPreference.query.filter_by(user_id=shipment.user_id, event_type=event_type).first()
            if not pref:
                logger.warning(f"No notification preferences found for user {shipment.user_id} event_type={event_type}")
                return

            providers = NotificationService.get_providers()
            
            if pref.in_app:
                providers['in_app'].send(event_type, shipment_id, message, context)
                
            if pref.whatsapp:
                providers['whatsapp'].send(event_type, shipment_id, message, context)
                
            if pref.email:
                providers['email'].send(event_type, shipment_id, message, context)
                
        except Exception as e:
            logger.error(f"Error triggering event {event_type} for shipment {shipment_id}: {e}")

    @staticmethod
    def create_notification(user_id: int, shipment_id: Optional[int], notification_type: str, message: str, channel: str = 'in_app') -> Notification:
        # Legacy method for direct creation, still used internally by InApp provider or old code
        try:
            notif = Notification(
                user_id=user_id,
                shipment_id=shipment_id,
                notification_type=notification_type,
                message=message,
                channel=channel,
                sent_at=datetime.now(timezone.utc)
            )
            db.session.add(notif)
            db.session.commit()
            return notif
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error creating notification: {e}")
            raise e

    @staticmethod
    def get_notifications(user_id: int, filters: Dict[str, Any] = None) -> List[Notification]:
        try:
            query = Notification.query.filter_by(user_id=user_id).order_by(Notification.created_at.desc())
            if filters:
                if 'status' in filters:
                    query = query.filter_by(status=filters['status'])
                if 'channel' in filters:
                    query = query.filter_by(channel=filters['channel'])
            return query.all()
        except Exception as e:
            logger.error(f"Error getting notifications: {e}")
            raise e

    @staticmethod
    def mark_as_read(user_id: int, notification_id: int) -> bool:
        try:
            notif = Notification.query.filter_by(user_id=user_id, id=notification_id).first()
            if notif:
                notif.status = 'read'
                db.session.commit()
                return True
            return False
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error marking notification {notification_id} as read: {e}")
            raise e

    @staticmethod
    def mark_all_as_read(user_id: int) -> int:
        try:
            notifs = Notification.query.filter_by(user_id=user_id, status='unread').all()
            count = len(notifs)
            for n in notifs:
                n.status = 'read'
            db.session.commit()
            return count
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error marking all notifications as read: {e}")
            raise e
