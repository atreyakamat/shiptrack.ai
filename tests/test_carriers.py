import pytest
from backend.carriers.mock import MockCarrierAdapter
from backend.carriers.india_post import IndiaPostAdapter
from backend.utils.validators import validate_tracking_number

def test_mock_adapter_valid_tracking():
    adapter = MockCarrierAdapter()
    data = adapter.track('EE123456789IN')
    assert data['details']['status'] == 'DELIVERED'

def test_mock_adapter_demo_shipments():
    adapter = MockCarrierAdapter()
    data = adapter.track('EM740043207IN')
    assert data['details']['status'] == 'OUT_FOR_DELIVERY'
    assert len(data['events']) == 3

def test_indiapost_adapter_validation():
    adapter = IndiaPostAdapter()
    with pytest.raises(ValueError):
        adapter.track('INVALID')

def test_status_mapping():
    adapter = IndiaPostAdapter()
    assert adapter.normalize_status('Item Delivery Confirmed') == 'DELIVERED'
    assert adapter.normalize_status('Out for Delivery') == 'OUT_FOR_DELIVERY'
