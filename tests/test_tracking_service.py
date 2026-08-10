import pytest
from backend.services.tracking_service import TrackingService
from backend.carriers.mock import MockCarrierAdapter
from backend.carriers.india_post import IndiaPostAdapter

def test_get_carrier_adapter():
    adapter = TrackingService.get_carrier_adapter('mock')
    assert isinstance(adapter, MockCarrierAdapter)

def test_mock_adapter_returns_valid_data():
    adapter = MockCarrierAdapter()
    data = adapter.track('EE123456789IN')
    assert 'events' in data
    assert len(data['events']) > 0

def test_status_normalization():
    adapter = IndiaPostAdapter()
    assert adapter.normalize_status('Item Delivered') == 'DELIVERED'
    assert adapter.normalize_status('Item Booked') == 'BOOKED'
    assert adapter.normalize_status('Bag Received') == 'IN_TRANSIT'
    assert adapter.normalize_status('Unknown Status') == 'UNKNOWN'
