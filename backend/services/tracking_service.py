import logging
from datetime import datetime, timezone
from typing import Dict, Any, List
from backend.extensions import db
from backend.models.shipment import Shipment
from backend.models.tracking_event import TrackingEvent
from backend.models.refresh_log import RefreshLog
from backend.carriers.mock import MockCarrierAdapter
from backend.carriers.india_post import IndiaPostAdapter
from .notification_service import NotificationService
import os

logger = logging.getLogger(__name__)

class TrackingService:
    @staticmethod
    def get_carrier_adapter(carrier: str):
        provider = os.getenv('TRACKING_PROVIDER', 'mock')
        demo_mode = os.getenv('TRACKING_DEMO_MODE', 'true').lower() == 'true'
        if demo_mode or provider == 'mock' or carrier == 'mock':
            return MockCarrierAdapter()
        if carrier == 'india_post':
            return IndiaPostAdapter()
        return MockCarrierAdapter()

    @staticmethod
    def deduplicate_events(shipment_id: int, new_events: List[Dict[str, Any]]) -> int:
        added_count = 0
        try:
            for event_data in new_events:
                existing = TrackingEvent.query.filter_by(
                    shipment_id=shipment_id,
                    event_date=event_data.get('date'),
                    event_time=event_data.get('time'),
                    status=event_data.get('status'),
                    location=event_data.get('location')
                ).first()
                if not existing:
                    new_event = TrackingEvent(
                        shipment_id=shipment_id,
                        event_date=event_data.get('date'),
                        event_time=event_data.get('time'),
                        status=event_data.get('status'),
                        location=event_data.get('location'),
                        raw_status=event_data.get('raw_status')
                    )
                    db.session.add(new_event)
                    added_count += 1
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error deduplicating events: {e}")
            raise e
        return added_count

    @staticmethod
    def refresh_shipment(shipment_id: int) -> Dict[str, Any]:
        # We need the shipment to know the user_id for the log
        shipment = db.session.query(Shipment).get(shipment_id)
        if not shipment:
            return {'status': 'error', 'error_message': 'Shipment not found'}
            
        log = RefreshLog(user_id=shipment.user_id, shipment_id=shipment_id, started_at=datetime.now(timezone.utc), status='processing')
        db.session.add(log)
        db.session.commit()
        
        try:
            # Row-level locking to prevent concurrent tracking refreshes on the same shipment
            shipment = db.session.query(Shipment).with_for_update().get(shipment_id)
            if not shipment:
                raise Exception("Shipment not found")
                
            adapter = TrackingService.get_carrier_adapter(shipment.carrier)
            tracking_data = adapter.track(shipment.tracking_number)
            
            if tracking_data:
                events = tracking_data.get('events', [])
                added_count = TrackingService.deduplicate_events(shipment_id, events)
                
                details = tracking_data.get('details', {})
                old_status = shipment.status
                new_status = details.get('status', old_status)
                
                shipment.status = new_status
                shipment.article_type = details.get('article_type', shipment.article_type)
                shipment.origin = details.get('origin', shipment.origin)
                shipment.destination = details.get('destination', shipment.destination)
                
                if events:
                    shipment.current_location = events[-1].get('location')
                    
                shipment.last_updated = datetime.now(timezone.utc)
                db.session.commit()
                
                db.session.commit()
                
                if old_status != new_status:
                    # Generic status change
                    NotificationService.trigger_event(
                        event_type='STATUS_CHANGED',
                        shipment_id=shipment_id,
                        message=f"Shipment {shipment.tracking_number} status changed to {new_status}",
                        context={'tracking_number': shipment.tracking_number, 'location': shipment.current_location}
                    )
                    
                    # Specific critical events
                    if new_status == 'OUT_FOR_DELIVERY':
                        NotificationService.trigger_event(
                            event_type='OUT_FOR_DELIVERY',
                            shipment_id=shipment_id,
                            message=f"Shipment {shipment.tracking_number} is out for delivery",
                            context={'tracking_number': shipment.tracking_number, 'location': shipment.current_location}
                        )
                    elif new_status == 'DELIVERED':
                        NotificationService.trigger_event(
                            event_type='DELIVERED',
                            shipment_id=shipment_id,
                            message=f"Shipment {shipment.tracking_number} has been delivered",
                            context={'tracking_number': shipment.tracking_number, 'location': shipment.current_location}
                        )
                    elif new_status in ['EXCEPTION', 'DELAYED']:
                        NotificationService.trigger_event(
                            event_type='DELAYED',
                            shipment_id=shipment_id,
                            message=f"Shipment {shipment.tracking_number} is experiencing delays or exceptions",
                            context={'tracking_number': shipment.tracking_number, 'location': shipment.current_location}
                        )
                
                log.status = 'success'
                log.events_found = added_count
            else:
                log.status = 'not_found'
                
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error refreshing shipment {shipment_id}: {e}")
            log.status = 'error'
            log.error_message = str(e)
            
            # Send refresh failed notification
            NotificationService.trigger_event(
                event_type='REFRESH_FAILED',
                shipment_id=shipment_id,
                message=f"Failed to refresh shipment {shipment_id}",
                context={'error': str(e)}
            )
            
        log.completed_at = datetime.now(timezone.utc)
        db.session.commit()
        return {'status': log.status, 'events_added': log.events_found}

    @staticmethod
    def refresh_all_active(user_id: int = None):
        query = Shipment.query.filter(
            Shipment.is_archived == False,
            Shipment.status != 'DELIVERED'
        )
        if user_id:
            query = query.filter_by(user_id=user_id)
        shipments = query.all()
        for shipment in shipments:
            try:
                TrackingService.refresh_shipment(shipment.id)
            except Exception as e:
                logger.error(f"Error in background refresh for {shipment.id}: {e}")
