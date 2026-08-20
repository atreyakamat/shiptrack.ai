"""
Unit & Integration Tests for Authorized Provider Tracking Adapter and Normalization Layer.
All fixtures are sanitized and clearly labeled as AUTHORIZED_PROVIDER_FIXTURE.
"""
import pytest
from unittest.mock import patch, MagicMock
from backend.carriers.authorized_tracking import AuthorizedTrackingAdapter
from backend.carriers.normalizer import CarrierNormalizer
from backend.carriers.base import BaseCarrierAdapter
from backend.services.tracking_service import TrackingService
from backend.models.tracking_event import TrackingEvent
from backend.models.shipment import Shipment
from backend.extensions import db

# ============================================================================
# AUTHORIZED PROVIDER TEST FIXTURES (Sanitized schema examples)
# ============================================================================

AUTHORIZED_PROVIDER_FIXTURE_SUCCESS = {
    "code": 200,
    "data": {
        "tracking_number": "EM740043207IN",
        "courier_code": "india-post",
        "delivery_status": "in_transit",
        "origin": "Panaji NSH (403001)",
        "destination": "Bambavada S.O (403107)",
        "events": [
            {
                "checkpoint_date": "2026-08-05T12:15:00+05:30",
                "raw_status": "Item Booked",
                "location": "Panaji NSH",
                "description": "Item Booked at Panaji NSH"
            },
            {
                "checkpoint_date": "2026-08-07T09:30:00+05:30",
                "raw_status": "Bag Received",
                "location": "Bambavada S.O",
                "description": "Bag Received at Bambavada S.O"
            }
        ]
    }
}

AUTHORIZED_PROVIDER_FIXTURE_DELIVERED = {
    "code": 200,
    "data": {
        "tracking_number": "EM740043207IN",
        "courier_code": "india-post",
        "delivery_status": "delivered",
        "origin": "Panaji NSH",
        "destination": "Bambavada S.O",
        "events": [
            {
                "checkpoint_date": "2026-08-07T14:30:00+05:30",
                "raw_status": "Item Delivered",
                "location": "Bambavada S.O",
                "description": "Item Delivered to Addressee"
            }
        ]
    }
}

AUTHORIZED_PROVIDER_FIXTURE_OUT_FOR_DELIVERY = {
    "code": 200,
    "data": {
        "tracking_number": "EM740043207IN",
        "courier_code": "india-post",
        "delivery_status": "out_for_delivery",
        "events": [
            {
                "checkpoint_date": "2026-08-07T08:00:00+05:30",
                "raw_status": "Out for Delivery",
                "location": "Bambavada S.O",
                "description": "Out for Delivery with Postman"
            }
        ]
    }
}

AUTHORIZED_PROVIDER_FIXTURE_MISSING_LOCATION = {
    "code": 200,
    "data": {
        "tracking_number": "EM740043207IN",
        "delivery_status": "in_transit",
        "events": [
            {
                "checkpoint_date": "2026-08-06T10:00:00+05:30",
                "raw_status": "In Transit",
                "location": None,
                "description": "Customs clearance in progress"
            }
        ]
    }
}

AUTHORIZED_PROVIDER_FIXTURE_UNKNOWN_STATUS = {
    "code": 200,
    "data": {
        "tracking_number": "EM740043207IN",
        "delivery_status": "custom_carrier_unmapped_state_xyz",
        "events": [
            {
                "checkpoint_date": "2026-08-06T10:00:00+05:30",
                "raw_status": "Unrecognized Event Code 999",
                "location": "Transit Hub"
            }
        ]
    }
}

# ============================================================================
# UNIT TESTS: CarrierNormalizer
# ============================================================================

def test_normalizer_status_mapping():
    assert CarrierNormalizer.normalize_status("Item Booked") == BaseCarrierAdapter.STATUS_BOOKED
    assert CarrierNormalizer.normalize_status("In Transit") == BaseCarrierAdapter.STATUS_IN_TRANSIT
    assert CarrierNormalizer.normalize_status("Bag Received") == BaseCarrierAdapter.STATUS_ARRIVED_AT_FACILITY
    assert CarrierNormalizer.normalize_status("Out for Delivery") == BaseCarrierAdapter.STATUS_OUT_FOR_DELIVERY
    assert CarrierNormalizer.normalize_status("Delivered") == BaseCarrierAdapter.STATUS_DELIVERED
    assert CarrierNormalizer.normalize_status("Delayed") == BaseCarrierAdapter.STATUS_DELAYED
    assert CarrierNormalizer.normalize_status("Unknown State 123") == BaseCarrierAdapter.STATUS_UNKNOWN
    assert CarrierNormalizer.normalize_status(None) == BaseCarrierAdapter.STATUS_UNKNOWN

def test_normalizer_success_response():
    result = CarrierNormalizer.normalize_response("EM740043207IN", AUTHORIZED_PROVIDER_FIXTURE_SUCCESS)
    details = result["details"]
    events = result["events"]
    
    assert details["tracking_number"] == "EM740043207IN"
    assert details["status"] == BaseCarrierAdapter.STATUS_IN_TRANSIT
    assert details["origin"] == "Panaji NSH (403001)"
    assert details["destination"] == "Bambavada S.O (403107)"
    assert len(events) == 2
    assert events[0]["date"] == "05/08/2026"
    assert events[0]["location"] == "Panaji NSH"
    assert events[1]["normalized_status"] == BaseCarrierAdapter.STATUS_ARRIVED_AT_FACILITY

def test_normalizer_delivered_response():
    result = CarrierNormalizer.normalize_response("EM740043207IN", AUTHORIZED_PROVIDER_FIXTURE_DELIVERED)
    assert result["details"]["status"] == BaseCarrierAdapter.STATUS_DELIVERED
    assert result["events"][0]["normalized_status"] == BaseCarrierAdapter.STATUS_DELIVERED

def test_normalizer_out_for_delivery_response():
    result = CarrierNormalizer.normalize_response("EM740043207IN", AUTHORIZED_PROVIDER_FIXTURE_OUT_FOR_DELIVERY)
    assert result["details"]["status"] == BaseCarrierAdapter.STATUS_OUT_FOR_DELIVERY
    assert result["events"][0]["normalized_status"] == BaseCarrierAdapter.STATUS_OUT_FOR_DELIVERY

def test_normalizer_missing_location_preserves_none():
    result = CarrierNormalizer.normalize_response("EM740043207IN", AUTHORIZED_PROVIDER_FIXTURE_MISSING_LOCATION)
    assert result["events"][0]["location"] is None
    assert result["events"][0]["description"] == "Customs clearance in progress"

def test_normalizer_unknown_status():
    result = CarrierNormalizer.normalize_response("EM740043207IN", AUTHORIZED_PROVIDER_FIXTURE_UNKNOWN_STATUS)
    assert result["details"]["status"] == BaseCarrierAdapter.STATUS_UNKNOWN
    assert result["events"][0]["normalized_status"] == BaseCarrierAdapter.STATUS_UNKNOWN

# ============================================================================
# UNIT TESTS: AuthorizedTrackingAdapter
# ============================================================================

def test_adapter_requires_api_key():
    adapter = AuthorizedTrackingAdapter(api_key="")
    with pytest.raises(ValueError, match="Live carrier tracking requires valid API credentials"):
        adapter.track("EM740043207IN")

def test_adapter_validates_tracking_number():
    adapter = AuthorizedTrackingAdapter(api_key="valid_key")
    assert adapter.validate_tracking_number("EM740043207IN") is True
    assert adapter.validate_tracking_number("INVALID123") is False
    with pytest.raises(ValueError, match="Invalid tracking number format"):
        adapter.track("INVALID123")

@patch("requests.post")
def test_adapter_successful_track_call(mock_post):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.content = b'{"data": {}}'
    mock_resp.json.return_value = AUTHORIZED_PROVIDER_FIXTURE_SUCCESS
    mock_post.return_value = mock_resp

    adapter = AuthorizedTrackingAdapter(api_key="valid_test_key", provider_name="trackingmore")
    result = adapter.track("EM740043207IN")
    
    assert result["details"]["status"] == BaseCarrierAdapter.STATUS_IN_TRANSIT
    assert len(result["events"]) == 2

@patch("requests.post")
def test_adapter_handles_auth_failure(mock_post):
    mock_resp = MagicMock()
    mock_resp.status_code = 401
    mock_resp.content = b'{"error": "Unauthorized"}'
    mock_resp.json.return_value = {"error": "Unauthorized"}
    mock_post.return_value = mock_resp

    adapter = AuthorizedTrackingAdapter(api_key="invalid_test_key", provider_name="trackingmore")
    with pytest.raises(PermissionError, match="Provider authentication failed"):
        adapter.track("EM740043207IN")

@patch("requests.post")
def test_adapter_handles_rate_limit(mock_post):
    mock_resp = MagicMock()
    mock_resp.status_code = 429
    mock_resp.content = b'{"error": "Too Many Requests"}'
    mock_resp.json.return_value = {"error": "Too Many Requests"}
    mock_post.return_value = mock_resp

    adapter = AuthorizedTrackingAdapter(api_key="test_key", provider_name="trackingmore")
    with pytest.raises(RuntimeError, match="Provider rate limit exceeded"):
        adapter.track("EM740043207IN")

@patch("requests.post")
def test_adapter_handles_provider_timeout(mock_post):
    import requests
    mock_post.side_effect = requests.exceptions.Timeout("Connection timed out")

    adapter = AuthorizedTrackingAdapter(api_key="test_key", provider_name="trackingmore")
    with pytest.raises(TimeoutError, match="Tracking provider timed out"):
        adapter.track("EM740043207IN")

# ============================================================================
# INTEGRATION TEST: TrackingService Event Deduplication with Normalized Data
# ============================================================================

def test_tracking_service_deduplication_with_normalized_events(app, test_user):
    with app.app_context():
        shipment = Shipment(
            user_id=test_user.id,
            tracking_number="EM740043207IN",
            carrier="india_post",
            status="BOOKED"
        )
        db.session.add(shipment)
        db.session.commit()

        # Step 1: Normalize events from fixture
        norm_result = CarrierNormalizer.normalize_response("EM740043207IN", AUTHORIZED_PROVIDER_FIXTURE_SUCCESS)
        events = norm_result["events"]

        # Step 2: Deduplicate & save events
        added_first = TrackingService.deduplicate_events(shipment.id, events)
        assert added_first == 2

        # Step 3: Check database records
        db_events = TrackingEvent.query.filter_by(shipment_id=shipment.id).all()
        assert len(db_events) == 2

        # Step 4: Run deduplication again with duplicate data
        added_second = TrackingService.deduplicate_events(shipment.id, events)
        assert added_second == 0 # Zero duplicate events inserted

        # Step 5: Add a new delivered event
        deliv_norm = CarrierNormalizer.normalize_response("EM740043207IN", AUTHORIZED_PROVIDER_FIXTURE_DELIVERED)
        added_third = TrackingService.deduplicate_events(shipment.id, deliv_norm["events"])
        assert added_third == 1

        total_db_events = TrackingEvent.query.filter_by(shipment_id=shipment.id).all()
        assert len(total_db_events) == 3
