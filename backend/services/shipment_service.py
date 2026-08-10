import logging
from typing import Dict, Any, List, Optional
from backend.extensions import db
from backend.models.shipment import Shipment
from backend.models.tracking_event import TrackingEvent

logger = logging.getLogger(__name__)

class ShipmentService:
    @staticmethod
    def create_shipment(data: Dict[str, Any]) -> Shipment:
        try:
            from backend.utils.validators import validate_tracking_number, normalize_tracking_number
            tracking_num = data.get('tracking_number')
            carrier = data.get('carrier', 'india_post')
            
            if not validate_tracking_number(tracking_num, carrier):
                raise ValueError("Invalid tracking number format")
                
            tracking_num = normalize_tracking_number(tracking_num)
            
            # Check if exists for this user
            existing = Shipment.query.filter_by(user_id=user_id, tracking_number=tracking_num, carrier=carrier).first()
            if existing:
                raise ValueError("Shipment already exists")
                
            shipment = Shipment(
                user_id=user_id,
                tracking_number=tracking_num,
                carrier=carrier,
                description=data.get('description'),
                category=data.get('category', 'general'),
                priority=data.get('priority', 'normal'),
                notes=data.get('notes'),
                status='BOOKED'
            )
            db.session.add(shipment)
            db.session.commit()
            
            # Trigger Notification
            from backend.services.notification_service import NotificationService
            NotificationService.trigger_event(
                event_type='SHIPMENT_ADDED',
                shipment_id=shipment.id,
                message=f"New shipment added: {shipment.tracking_number}",
                context={'tracking_number': shipment.tracking_number}
            )
            
            return shipment
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error creating shipment: {e}")
            raise e

    @staticmethod
    def get_shipment(user_id: int, shipment_id: int) -> Optional[Shipment]:
        try:
            return Shipment.query.filter_by(id=shipment_id, user_id=user_id).first()
        except Exception as e:
            logger.error(f"Error getting shipment {shipment_id}: {e}")
            raise e

    @staticmethod
    def get_all_shipments(user_id: int, filters: Dict[str, Any] = None) -> List[Shipment]:
        try:
            query = Shipment.query.filter_by(user_id=user_id, is_archived=False)
            if filters:
                if 'status' in filters:
                    query = query.filter_by(status=filters['status'])
                if 'carrier' in filters:
                    query = query.filter_by(carrier=filters['carrier'])
                if 'category' in filters:
                    query = query.filter_by(category=filters['category'])
            return query.all()
        except Exception as e:
            logger.error(f"Error getting shipments: {e}")
            raise e

    @staticmethod
    def update_shipment(user_id: int, shipment_id: int, data: Dict[str, Any]) -> Optional[Shipment]:
        try:
            shipment = Shipment.query.filter_by(id=shipment_id, user_id=user_id).first()
            if not shipment:
                return None
            for key, value in data.items():
                if hasattr(shipment, key):
                    setattr(shipment, key, value)
            db.session.commit()
            return shipment
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error updating shipment {shipment_id}: {e}")
            raise e

    @staticmethod
    def delete_shipment(user_id: int, shipment_id: int) -> bool:
        try:
            shipment = Shipment.query.filter_by(id=shipment_id, user_id=user_id).first()
            if not shipment:
                return False
            db.session.delete(shipment)
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error deleting shipment {shipment_id}: {e}")
            raise e

    @staticmethod
    def archive_shipment(user_id: int, shipment_id: int, archive: bool = True) -> bool:
        try:
            shipment = Shipment.query.filter_by(id=shipment_id, user_id=user_id).first()
            if not shipment:
                return False
            shipment.is_archived = archive
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error archiving shipment {shipment_id}: {e}")
            raise e

    @staticmethod
    def search_shipments(user_id: int, query_str: str) -> List[Shipment]:
        try:
            search = f"%{query_str}%"
            return Shipment.query.filter(
                (Shipment.tracking_number.ilike(search)) |
                (Shipment.description.ilike(search)) |
                (Shipment.current_location.ilike(search))
            ).filter_by(user_id=user_id, is_archived=False).all()
        except Exception as e:
            logger.error(f"Error searching shipments: {e}")
            raise e

    @staticmethod
    def get_shipments_needing_refresh(user_id: Optional[int] = None) -> List[Shipment]:
        try:
            query = Shipment.query.filter(
                Shipment.is_archived == False,
                Shipment.status.notin_(['DELIVERED', 'EXCEPTION'])
            )
            if user_id:
                query = query.filter_by(user_id=user_id)
            return query.all()
        except Exception as e:
            logger.error(f"Error getting shipments for refresh: {e}")
            raise e
