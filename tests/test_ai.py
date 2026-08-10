import pytest
from backend.services.ai_service import AIService
from backend.models.shipment import Shipment
from backend.models.tracking_event import TrackingEvent
from datetime import datetime, timezone, timedelta
from backend.extensions import db

def test_classify_health(app):
    with app.app_context():
        s = Shipment(tracking_number="AA123456789IN", status="IN_TRANSIT")
        db.session.add(s)
        db.session.commit()
        
        # No events -> NORMAL
        assert AIService.classify_health(s) == 'NORMAL'
        
        # Event 1 day ago -> WATCH
        e1 = TrackingEvent(shipment_id=s.id, status="IN_TRANSIT", created_at=datetime.now(timezone.utc) - timedelta(days=2))
        db.session.add(e1)
        db.session.commit()
        assert AIService.classify_health(s) == 'WATCH'
        
        # Event 4 days ago -> DELAYED
        e1.created_at = datetime.now(timezone.utc) - timedelta(days=4)
        db.session.commit()
        assert AIService.classify_health(s) == 'DELAYED'
        
        # Status DELIVERED -> DELIVERED
        s.status = 'DELIVERED'
        db.session.commit()
        assert AIService.classify_health(s) == 'DELIVERED'

def test_generate_summary_no_hallucination(app):
    with app.app_context():
        s = Shipment(tracking_number="BB123456789IN", status="BOOKED")
        db.session.add(s)
        db.session.commit()
        
        e = TrackingEvent(shipment_id=s.id, status="BOOKED", location="Mumbai", created_at=datetime.now(timezone.utc))
        db.session.add(e)
        db.session.commit()
        
        summary = AIService.generate_summary(s)
        assert "Mumbai" in summary['summary']
        assert "BOOKED" in summary['summary'] or "booked" in summary['summary']
        # Shouldn't invent Delhi
        assert "Delhi" not in summary['summary']
