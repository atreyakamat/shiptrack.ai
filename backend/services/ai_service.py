import logging
import os
from datetime import datetime, timezone
from typing import Dict, Any, List
from backend.extensions import db
from backend.models.shipment import Shipment
from backend.models.ai_summary import AISummary
from backend.models.tracking_event import TrackingEvent

logger = logging.getLogger(__name__)

class AIService:
    @staticmethod
    def get_provider():
        return os.getenv('AI_PROVIDER', 'mock')

    @staticmethod
    def classify_health(shipment: Shipment) -> str:
        if shipment.status == 'DELIVERED':
            return 'DELIVERED'
        
        events = TrackingEvent.query.filter_by(shipment_id=shipment.id).order_by(TrackingEvent.created_at.desc()).all()
        if not events:
            return 'NORMAL'
            
        last_event_time = events[0].created_at
        if not last_event_time:
            return 'NORMAL'
            
        days_since_update = (datetime.now(timezone.utc) - last_event_time.replace(tzinfo=timezone.utc)).days
        
        if days_since_update > 3:
            return 'DELAYED'
        elif days_since_update > 1:
            return 'WATCH'
        return 'NORMAL'

    @staticmethod
    def generate_summary(shipment: Shipment) -> Dict[str, Any]:
        try:
            provider = AIService.get_provider()
            events = TrackingEvent.query.filter_by(shipment_id=shipment.id).order_by(TrackingEvent.id.asc()).all()
            
            health = AIService.classify_health(shipment)
            
            # Interpretive rule-based mock for all providers initially
            status = shipment.status
            last_location = events[-1].location if events else 'Unknown Location'
            
            if status == 'DELIVERED':
                summary_text = f"Your parcel was successfully delivered at {last_location}."
                prediction = "Already delivered."
            elif status == 'OUT_FOR_DELIVERY':
                summary_text = f"Your parcel has reached the destination delivery office and is currently out for delivery in {last_location}. Expect it today!"
                prediction = "Delivery expected today."
            elif status == 'IN_TRANSIT':
                summary_text = f"Your parcel is steadily making its way through the network. It was last processed at {last_location}."
                prediction = "Expected delivery in 1-2 days based on current progress."
            elif status == 'BOOKED':
                summary_text = f"Your parcel has been booked at {last_location} and is awaiting dispatch."
                prediction = "Expected delivery in 3-5 days."
            else:
                summary_text = f"Shipment {shipment.tracking_number} is currently {status}. Last seen at {last_location}."
                prediction = "Awaiting more data."
                
            delay_analysis = "No significant delays detected."
            if health == 'DELAYED':
                delay_analysis = "Shipment appears delayed. There have been no tracking updates for over 3 days, which is unusual."
            elif health == 'WATCH':
                delay_analysis = "Shipment is progressing slower than usual, but is still moving."

            summary = AISummary.query.filter_by(shipment_id=shipment.id).first()
            if not summary:
                summary = AISummary(shipment_id=shipment.id)
                db.session.add(summary)
            
            summary.summary = summary_text
            summary.delay_analysis = delay_analysis
            summary.prediction = prediction
            summary.health_status = health
            summary.model = provider
            db.session.commit()
            
            return summary.to_dict()
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error generating AI summary for {shipment.id}: {e}")
            raise e

    @staticmethod
    def generate_insights(shipments: List[Shipment]) -> Dict[str, Any]:
        return {
            "insight": f"Analyzed {len(shipments)} shipments. System is operating normally.",
            "recommendations": ["Monitor delayed shipments."]
        }
