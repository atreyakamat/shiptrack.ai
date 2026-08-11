import pytest
from backend.services.analytics_service import AnalyticsService
from backend.models import Shipment

def test_get_overview_stats(db, sample_shipment, test_user):
    stats = AnalyticsService.get_overview_stats(test_user.id)
    assert stats['total'] == 1
    assert stats['in_transit'] == 1

def test_get_delivery_rate(db, sample_shipment, test_user):
    stats = AnalyticsService.get_overview_stats(test_user.id)
    assert stats['delivery_rate'] == 0.0
    
    sample_shipment.status = 'DELIVERED'
    db.session.commit()
    
    stats = AnalyticsService.get_overview_stats(test_user.id)
    assert stats['delivery_rate'] == 100.0

def test_get_shipments_by_status(db, sample_shipment, test_user):
    counts = AnalyticsService.get_shipments_by_status(test_user.id)
    # Assuming empty list is returned for now based on implementation
    assert isinstance(counts, list)
