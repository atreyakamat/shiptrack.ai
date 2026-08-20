import pytest
from datetime import datetime, timezone, timedelta
from backend.app import create_app
from backend.extensions import db
from backend.models.user import User
from backend.models.shipment import Shipment
from backend.models.tracking_event import TrackingEvent
from backend.models.postal_office import PostalOffice
from backend.services.shipment_service import ShipmentService
from backend.services.tracking_service import TrackingService
from backend.services.analytics_service import AnalyticsService
from backend.services.ai_service import AIService
from backend.services.ocr_service import OCRService

def test_empty_state_analytics(app, test_user):
    """STEP 4 & 10: Verify empty state analytics for a new user with 0 shipments."""
    with app.app_context():
        stats = AnalyticsService.get_overview_stats(test_user.id)
        assert stats['total'] == 0
        assert stats['delivered'] == 0
        assert stats['delivery_rate'] == 0.0
        assert stats['avg_time'] == 0
        
        by_status = AnalyticsService.get_shipments_by_status(test_user.id)
        assert by_status == []
        
        over_time = AnalyticsService.get_shipments_over_time(test_user.id)
        assert len(over_time) == 6
        assert all(d['count'] == 0 for d in over_time)
        
        dist = AnalyticsService.get_delivery_time_distribution(test_user.id)
        assert dist == []
        
        carrier_times = AnalyticsService.get_avg_delivery_time_by_carrier(test_user.id)
        assert carrier_times == []
        
        stale = AnalyticsService.get_stale_shipments(test_user.id)
        assert stale == []
        
        activity = AnalyticsService.get_recent_activity(test_user.id)
        assert activity == []

def test_empty_state_ai_insights(app, test_user):
    """STEP 8 & 10: Verify AI insights handling for 0 shipments."""
    with app.app_context():
        insights = AIService.generate_insights([])
        assert insights['total_count'] == 0
        assert "No active shipments found" in insights['summary']
        assert insights['delayed_shipments'] == []

def test_ai_grounding_truthful_statements(app, test_user):
    """STEP 8: Verify AI insights only interpret structured data without hallucinated claims."""
    with app.app_context():
        s = Shipment(
            user_id=test_user.id,
            tracking_number="EM740043207IN",
            carrier="india_post",
            status="OUT_FOR_DELIVERY",
            current_location="Bambavada S.O"
        )
        db.session.add(s)
        db.session.commit()
        
        ev = TrackingEvent(
            shipment_id=s.id,
            event_date="07/08/2026",
            event_time="02:15 PM",
            status="OUT_FOR_DELIVERY",
            location="Bambavada S.O"
        )
        db.session.add(ev)
        db.session.commit()
        
        summary = AIService.generate_summary(s)
        assert "Bambavada S.O" in summary['summary']
        assert "out for delivery" in summary['summary'].lower()
        # Verify no unsupported claims like live GPS or exact arrival hours
        assert "live gps" not in summary['summary'].lower()
        assert "definitely" not in summary['summary'].lower()

def test_map_facility_geocoding_and_unknown_fallback(app, test_user):
    """STEP 7: Verify map coordinates only use known PostalOffice lookups without guessing."""
    with app.app_context():
        po = PostalOffice(name="Panaji NSH", code="403001", city="Panaji", state="Goa", latitude=15.4989, longitude=73.8278)
        db.session.add(po)
        db.session.commit()
        
        s = Shipment(user_id=test_user.id, tracking_number="EM123456789IN", carrier="india_post")
        db.session.add(s)
        db.session.commit()
        
        events = [
            {'date': '08/08/2026', 'time': '10:00 AM', 'status': 'IN_TRANSIT', 'location': 'Panaji NSH', 'raw_status': 'Bag Received'},
            {'date': '09/08/2026', 'time': '12:00 PM', 'status': 'IN_TRANSIT', 'location': 'Unknown Foreign Hub S.O', 'raw_status': 'Received'}
        ]
        
        TrackingService.deduplicate_events(s.id, events)
        
        saved_events = TrackingEvent.query.filter_by(shipment_id=s.id).order_by(TrackingEvent.id.asc()).all()
        assert len(saved_events) == 2
        # Known hub gets accurate coordinates
        assert saved_events[0].latitude == 15.4989
        assert saved_events[0].longitude == 73.8278
        # Unknown hub does NOT invent coordinates
        assert saved_events[1].latitude is None
        assert saved_events[1].longitude is None

def test_ocr_candidate_deduplication_and_sorting():
    """STEP 2: Verify OCR extracts multiple candidates, deduplicates, and sorts by confidence."""
    text = "SLIP: EM740043207IN REF: EE123456789IN DUP: EM740043207IN LOOSE: SS12345678OIN"
    candidates = OCRService.extract_candidates(text)
    
    # Should be 3 unique candidates
    nums = [c['tracking_number'] for c in candidates]
    assert len(candidates) == 3
    assert nums == ["EM740043207IN", "EE123456789IN", "SS123456780IN"]
    # Strict matches (0.95) should be sorted ahead of loose matches (0.60)
    assert candidates[0]['confidence'] == 0.95
    assert candidates[1]['confidence'] == 0.95
    assert candidates[2]['confidence'] == 0.60

def test_provider_failure_preserves_shipment_data(auth_client, app, test_user, monkeypatch):
    """STEP 5 & 6: Verify provider failure returns 503 and preserves previous data."""
    with app.app_context():
        s = Shipment(
            user_id=test_user.id,
            tracking_number="EM999999999IN",
            carrier="india_post",
            status="IN_TRANSIT",
            current_location="Panaji NSH"
        )
        db.session.add(s)
        db.session.commit()
        sid = s.id
        
        ev = TrackingEvent(
            shipment_id=sid,
            event_date="01/08/2026",
            event_time="10:00 AM",
            status="IN_TRANSIT",
            location="Panaji NSH"
        )
        db.session.add(ev)
        db.session.commit()
        
    # Mock refresh to fail with provider unavailable
    def mock_refresh_fail(shipment_id):
        return {
            'status': 'error',
            'events_added': 0,
            'error_message': 'Live India Post tracking requires an authorized tracking integration.'
        }
    monkeypatch.setattr(TrackingService, 'refresh_shipment', mock_refresh_fail)
    
    rv = auth_client.post(f'/api/shipments/{sid}/refresh')
    assert rv.status_code == 503
    data = rv.get_json()
    assert data['success'] is False
    assert data['error']['code'] == 'PROVIDER_UNAVAILABLE'
    
    # Existing data must remain completely intact
    with app.app_context():
        reloaded = Shipment.query.get(sid)
        assert reloaded.status == "IN_TRANSIT"
        assert reloaded.current_location == "Panaji NSH"
        events_count = TrackingEvent.query.filter_by(shipment_id=sid).count()
        assert events_count == 1

def test_tenant_isolation_comprehensive(app):
    """STEP 9: Comprehensive cross-tenant access denial."""
    with app.app_context():
        user_a = User(email="user_a@shiptrack.ai", password_hash="hash_a")
        user_b = User(email="user_b@shiptrack.ai", password_hash="hash_b")
        db.session.add_all([user_a, user_b])
        db.session.commit()
        
        shipment_b = Shipment(user_id=user_b.id, tracking_number="EB112233445IN", carrier="india_post")
        db.session.add(shipment_b)
        db.session.commit()
        
        # User A cannot read User B shipment via service
        assert ShipmentService.get_shipment(user_a.id, shipment_b.id) is None
        
        # User A cannot update User B shipment
        assert ShipmentService.update_shipment(user_a.id, shipment_b.id, {'description': 'Hacked'}) is None
        
        # User A cannot delete User B shipment
        assert ShipmentService.delete_shipment(user_a.id, shipment_b.id) is False
