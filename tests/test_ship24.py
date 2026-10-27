"""Unit tests for the Ship24 adapter (HTTP mocked — no network)."""
from unittest.mock import patch, MagicMock
import pytest
from backend.carriers.ship24 import Ship24Adapter
from backend.carriers.base import BaseCarrierAdapter

SHIP24_PAYLOAD = {
    "data": {"trackings": [{
        "tracker": {"trackerId": "trk-123"},
        "shipment": {"statusMilestone": "in_transit"},
        "events": [
            {"status": "Item Kept on Hold", "occurrenceDatetime": "2026-10-26T19:26:43",
             "location": "Tivim S.O", "statusMilestone": "in_transit"},
            {"status": "Taken out for delivery", "occurrenceDatetime": "2026-10-26T10:56:27",
             "location": "Tivim S.O", "statusMilestone": "out_for_delivery"},
            {"status": "Item Booked", "occurrenceDatetime": "2026-10-22T17:35:49",
             "location": "Goregaon RS SO", "statusMilestone": "info_received"},
        ],
    }]}
}


def _mock_resp(json_data, status=200):
    m = MagicMock()
    m.status_code = status
    m.json.return_value = json_data
    m.raise_for_status.return_value = None
    return m


def test_track_normalizes_ship24_payload():
    with patch("backend.carriers.ship24.requests.post", return_value=_mock_resp(SHIP24_PAYLOAD)):
        r = Ship24Adapter(api_key="k").track("EY672780687IN")
    ev, d = r["events"], r["details"]
    assert len(ev) == 3
    # Stored earliest-first with DD/MM/YYYY dates (matches the web adapter for dedup).
    assert ev[0]["status"] == "Item Booked"
    assert ev[0]["date"] == "22/10/2026"
    assert ev[0]["time"] == "17:35:49"
    assert ev[-1]["status"] == "Item Kept on Hold"
    # Latest event "on hold" -> EXCEPTION, overriding Ship24's 'in_transit' milestone.
    assert d["status"] == BaseCarrierAdapter.STATUS_EXCEPTION
    assert d["origin"] == "Goregaon RS SO"
    assert d["tracker_id"] == "trk-123"


def test_get_latest_location_is_newest_event():
    with patch("backend.carriers.ship24.requests.post", return_value=_mock_resp(SHIP24_PAYLOAD)):
        a = Ship24Adapter(api_key="k")
        r = a.track("EY672780687IN")
        assert a.get_latest_location(r["events"]) == "Tivim S.O"


def test_delivered_milestone_maps_to_delivered():
    payload = {"data": {"trackings": [{
        "tracker": {"trackerId": "t"}, "shipment": {"statusMilestone": "delivered"},
        "events": [{"status": "Delivered", "occurrenceDatetime": "2026-10-20T10:00:00",
                    "location": "Mumbai", "statusMilestone": "delivered"}]}]}}
    with patch("backend.carriers.ship24.requests.post", return_value=_mock_resp(payload)):
        r = Ship24Adapter(api_key="k").track("XX1IN")
    assert r["details"]["status"] == BaseCarrierAdapter.STATUS_DELIVERED


def test_no_trackings_returns_empty():
    with patch("backend.carriers.ship24.requests.post", return_value=_mock_resp({"data": {"trackings": []}})):
        r = Ship24Adapter(api_key="k").track("XX1IN")
    assert r["events"] == []
    assert r["details"]["status"] == BaseCarrierAdapter.STATUS_UNKNOWN


def test_missing_api_key_raises():
    a = Ship24Adapter(api_key="x")
    a.api_key = ""  # simulate no key configured (constructor falls back to env in prod)
    with pytest.raises(ValueError):
        a.active_tracker_count()


def test_auth_failure_raises_permission_error():
    with patch("backend.carriers.ship24.requests.post", return_value=_mock_resp({}, status=401)):
        with pytest.raises(PermissionError):
            Ship24Adapter(api_key="bad").track("XX1IN")
