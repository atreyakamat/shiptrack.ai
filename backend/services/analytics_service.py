import logging
from typing import Dict, Any, List
from backend.models.shipment import Shipment
from sqlalchemy import func

logger = logging.getLogger(__name__)

class AnalyticsService:
    @staticmethod
    def get_overview_stats(user_id: int) -> Dict[str, Any]:
        try:
            base_query = Shipment.query.filter_by(user_id=user_id, is_archived=False)
            total = base_query.count()
            in_transit = base_query.filter_by(status='IN_TRANSIT').count()
            delivered = base_query.filter_by(status='DELIVERED').count()
            delayed = base_query.filter_by(status='DELAYED').count()
            
            delivery_rate = 0.0
            if total > 0:
                delivery_rate = round((delivered / total) * 100, 1)
                
            return {
                'total': total,
                'in_transit': in_transit,
                'delivered': delivered,
                'delayed': delayed,
                'delivery_rate': delivery_rate,
                'avg_time': 3.5 # Dummy value for now as we don't have enough data
            }
        except Exception as e:
            logger.error(f"Error getting overview stats: {e}")
            return {'total': 0, 'in_transit': 0, 'delivered': 0, 'delayed': 0, 'delivery_rate': 0.0, 'avg_time': 0}

    @staticmethod
    def get_shipments_by_status() -> List[Dict[str, Any]]:
        try:
            results = []
            # Simple count by status
            return results
        except Exception as e:
            logger.error(f"Error getting shipments by status: {e}")
            return []
