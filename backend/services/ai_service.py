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
                summary_text = f"Your parcel is currently out for delivery in {last_location}. It may be delivered today based on its current status."
                prediction = "Current status suggests delivery may occur today, but no confirmed delivery date is available."
            elif status == 'ARRIVED_AT_FACILITY':
                summary_text = f"Your parcel has arrived at a sorting facility or post office in {last_location}."
                prediction = "Awaiting dispatch to the next location."
            elif status == 'IN_TRANSIT':
                summary_text = f"Your parcel is steadily making its way through the network. It was last processed at {last_location}."
                prediction = "Transit is ongoing based on current progress."
            elif status == 'DISPATCHED':
                summary_text = f"Your parcel has been dispatched from {last_location}."
                prediction = "Moving to the next facility."
            elif status == 'BOOKED':
                summary_text = f"Your parcel has been booked at {last_location} and is awaiting dispatch."
                prediction = "Awaiting movement."
            elif status == 'DELAYED' or status == 'EXCEPTION':
                summary_text = f"Your parcel encountered a delay or exception. Last known location is {last_location}."
                prediction = "Delivery may be delayed."
            elif status == 'RETURNED':
                summary_text = f"Your parcel is being returned. Last scan at {last_location}."
                prediction = "Return in progress."
            else:
                summary_text = f"Shipment {shipment.tracking_number} is currently {status}. Last seen at {last_location}."
                prediction = "Awaiting more data."
                
            delay_analysis = "Insufficient tracking history to assess delays."
            if len(events) > 1 and health == 'NORMAL':
                delay_analysis = "No significant delays detected."
            elif health == 'DELAYED':
                delay_analysis = "Shipment appears delayed. There have been no tracking updates for over 3 days, which is unusual."
            elif health == 'WATCH':
                delay_analysis = "Shipment is progressing slower than usual, but is still moving."

            summary = AISummary.query.filter_by(shipment_id=shipment.id, user_id=shipment.user_id).first()
            if not summary:
                summary = AISummary(shipment_id=shipment.id, user_id=shipment.user_id)
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
