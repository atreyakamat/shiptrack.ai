import logging
from typing import Dict, Any, List, Optional
from backend.extensions import db
from backend.models.shipment import Shipment
from backend.models.tracking_event import TrackingEvent

logger = logging.getLogger(__name__)

class ShipmentService:
    @staticmethod
    def create_shipment(user_id: int, data: Dict[str, Any]) -> Shipment:
        try:
            from backend.utils.validators import validate_tracking_number, normalize_tracking_number, normalize_carrier, validate_carrier
            tracking_num = data.get('tracking_number')
            carrier = normalize_carrier(data.get('carrier', ''))
            
            if not tracking_num:
                raise ValueError("Tracking number is required")
                
            if not carrier or not validate_carrier(carrier):
                raise ValueError("Valid carrier is required")
            
            if not validate_tracking_number(tracking_num, carrier):
                raise ValueError("Invalid tracking number format")
                
            category = data.get('category', 'General')
            priority = data.get('priority', 'Normal')
            if category not in ['General', 'Documents', 'Package', 'Government', 'Legal', 'Personal', 'Business']:
                raise ValueError("Invalid category")
            if priority not in ['Normal', 'Low', 'High', 'Urgent']:
                raise ValueError("Invalid priority")
                
            description = data.get('description', '')
            notes = data.get('notes', '')
            if description and len(description) > 500:
                raise ValueError("Description is too long (max 500 characters)")
            if notes and len(notes) > 5000:
                raise ValueError("Notes are too long (max 5000 characters)")
                
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
            try:
                from backend.services.notification_service import NotificationService
                NotificationService.trigger_event(
                    event_type='SHIPMENT_ADDED',
                    shipment_id=shipment.id,
                    message=f"New shipment added: {shipment.tracking_number}",
                    context={'tracking_number': shipment.tracking_number}
                )
            except Exception as notify_err:
                logger.warning(f"Notification failed for {shipment.id}: {notify_err}")
            
            return shipment
        except Exception as e:
            db.session.rollback()
            # If the database enforces a unique constraint that we hit
            import sqlalchemy.exc
            if isinstance(e, sqlalchemy.exc.IntegrityError):
                logger.error(f"IntegrityError creating shipment (duplicate): {e}")
                raise ValueError("Shipment already exists")
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
