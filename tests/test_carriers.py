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


def test_normalizer_handles_trackingmore_v4_items_payload():
    from backend.carriers.normalizer import CarrierNormalizer
    payload = {"meta": {"code": 200}, "data": {"items": [{
        "delivery_status": "transit",
        "origin_info": {"trackinfo": [
            {"checkpoint_date": "2026-08-09T02:00:00", "tracking_detail": "Item Dispatched", "location": "Pune"},
            {"checkpoint_date": "2026-08-08T10:00:00", "tracking_detail": "Item Booked", "location": "Mumbai GPO"},
        ]},
    }]}}
    out = CarrierNormalizer.normalize_response("EM123456789IN", payload)
    assert len(out['events']) == 2
    assert out['events'][0]['status'] == 'Item Dispatched'
    assert out['events'][0]['location'] == 'Pune'
