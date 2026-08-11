import logging
from typing import Dict, Any, List
from backend.models.shipment import Shipment
from backend.models.tracking_event import TrackingEvent
from backend.extensions import db
from sqlalchemy import func
from datetime import datetime

logger = logging.getLogger(__name__)

class AnalyticsService:
    @staticmethod
    def get_overview_stats(user_id: int) -> Dict[str, Any]:
        try:
            base_query = Shipment.query.filter_by(user_id=user_id, is_archived=False)
            total = base_query.count()
            in_transit = base_query.filter_by(status='IN_TRANSIT').count()
            delivered = base_query.filter_by(status='DELIVERED').count()
            delayed = base_query.filter(Shipment.status.in_(['DELAYED', 'EXCEPTION'])).count()
            
            delivery_rate = 0.0
            if total > 0:
                delivery_rate = round((delivered / total) * 100, 1)
                
            # Calculate average time in days using python to remain DB agnostic
            delivered_shipments = base_query.filter_by(status='DELIVERED').all()
            total_days = 0
            valid_times = 0
            for s in delivered_shipments:
                if s.created_at and s.updated_at:
                    days = (s.updated_at - s.created_at).total_seconds() / (24 * 3600)
                    if days > 0:
                        total_days += days
                        valid_times += 1
                        
            avg_time = round(total_days / valid_times, 1) if valid_times > 0 else 0
                
            return {
                'total': total,
                'in_transit': in_transit,
                'delivered': delivered,
                'delayed': delayed,
                'delivery_rate': delivery_rate,
                'avg_time': avg_time
            }
        except Exception as e:
            logger.error(f"Error getting overview stats: {e}")
            return {'total': 0, 'in_transit': 0, 'delivered': 0, 'delayed': 0, 'delivery_rate': 0.0, 'avg_time': 0}

    @staticmethod
    def get_shipments_by_status(user_id: int) -> List[Dict[str, Any]]:
        try:
            results = db.session.query(Shipment.status, func.count(Shipment.id)).filter_by(user_id=user_id, is_archived=False).group_by(Shipment.status).all()
            return [{'status': r[0], 'count': r[1]} for r in results]
        except Exception as e:
            logger.error(f"Error getting shipments by status: {e}")
            return []

    @staticmethod
    def get_common_locations(user_id: int) -> List[Dict[str, Any]]:
        try:
            results = db.session.query(TrackingEvent.location, func.count(TrackingEvent.id)).join(Shipment).filter(Shipment.user_id == user_id).group_by(TrackingEvent.location).order_by(func.count(TrackingEvent.id).desc()).limit(5).all()
            return [{'location': r[0] if r[0] else 'Unknown', 'count': r[1]} for r in results]
        except Exception as e:
            logger.error(f"Error getting common locations: {e}")
            return []
