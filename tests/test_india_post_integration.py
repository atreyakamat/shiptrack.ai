"""
Integration tests for the India Post human-assisted tracking path.

These exercise the full chain WITHOUT a real browser or network:
  extract_table_data (de-obfuscation)  ->  TrackingService.refresh_shipment  ->  DB

The browser + human CAPTCHA step is the only part stubbed out (via a patched
adapter.track), because that step is interactive by design and must stay so.
"""
import pytest
from unittest.mock import patch

from backend.carriers.india_post_web import IndiaPostWebAdapter
from backend.carriers.base import BaseCarrierAdapter
from backend.services.tracking_service import TrackingService
from backend.models import Shipment, TrackingEvent
from tests.india_post_fixtures import build_india_post_page, ON_HOLD_EVENTS, DELIVERED_EVENTS


@pytest.fixture
def india_post_shipment(db, test_user):
    s = Shipment(user_id=test_user.id, tracking_number="EY672780687IN",
                 carrier="india_post", status="UNKNOWN")
    db.session.add(s)
    db.session.commit()
    return s


def _canonical(html: str, tn: str):
    """What adapter.track() returns once a human has solved the CAPTCHA."""
    return IndiaPostWebAdapter().extract_table_data(html, tn)


def test_refresh_persists_clean_events_end_to_end(app, db, india_post_shipment):
    """A solved lookup flows into the DB as clean, decoy-free events and updates status."""
    html = build_india_post_page(events=ON_HOLD_EVENTS)
    sid = india_post_shipment.id
    app.config["TRACKING_PROVIDER"] = "web"
    app.config["TRACKING_DEMO_MODE"] = False
    with patch.object(IndiaPostWebAdapter, "track",
                      return_value=_canonical(html, "EY672780687IN")):
        result = TrackingService.refresh_shipment(sid)
    db.session.expire_all()

    assert result["status"] == "success"
    stored = TrackingEvent.query.filter_by(shipment_id=sid).all()
    assert len(stored) == len(ON_HOLD_EVENTS)
    # No decoy text persisted.
    for ev in stored:
        assert "XX" not in (ev.status or "")
        assert "XX" not in (ev.location or "")
    refreshed = db.session.get(Shipment, sid)
    assert refreshed.status == BaseCarrierAdapter.STATUS_EXCEPTION
    assert refreshed.origin == "Goregaon RS SO"
    assert refreshed.destination == "Tivim S.O"
    assert refreshed.current_location == "Tivim S.O"


def test_refresh_sets_delivered_status(app, db, india_post_shipment):
    html = build_india_post_page(events=DELIVERED_EVENTS, booked_at="Panaji NSH",
                                 destination="Bambavada S.O", article_type="Speed Post")
    sid = india_post_shipment.id
    app.config["TRACKING_PROVIDER"] = "web"
    app.config["TRACKING_DEMO_MODE"] = False
    with patch.object(IndiaPostWebAdapter, "track",
                      return_value=_canonical(html, "EY672780687IN")):
        TrackingService.refresh_shipment(sid)
    db.session.expire_all()
    assert db.session.get(Shipment, sid).status == BaseCarrierAdapter.STATUS_DELIVERED


def test_refresh_is_idempotent_no_duplicate_events(app, db, india_post_shipment):
    """Running the same solved lookup twice must not double the stored events."""
    html = build_india_post_page(events=ON_HOLD_EVENTS)
    sid = india_post_shipment.id
    app.config["TRACKING_PROVIDER"] = "web"
    app.config["TRACKING_DEMO_MODE"] = False
    with patch.object(IndiaPostWebAdapter, "track",
                      return_value=_canonical(html, "EY672780687IN")):
        TrackingService.refresh_shipment(sid)
        TrackingService.refresh_shipment(sid)
    db.session.expire_all()
    assert TrackingEvent.query.filter_by(shipment_id=sid).count() == len(ON_HOLD_EVENTS)


def test_provider_selection_routes_to_web_adapter(app):
    with app.app_context():
        app.config["TRACKING_DEMO_MODE"] = False
        app.config["TRACKING_PROVIDER"] = "web"
        adapter = TrackingService.get_carrier_adapter("india_post")
        assert isinstance(adapter, IndiaPostWebAdapter)


def test_closed_window_surfaces_friendly_error(app, db, india_post_shipment):
    """If the user closes the India Post window, refresh fails cleanly, not with a raw crash."""
    sid = india_post_shipment.id
    app.config["TRACKING_PROVIDER"] = "web"
    app.config["TRACKING_DEMO_MODE"] = False
    with patch.object(IndiaPostWebAdapter, "track",
                      side_effect=ConnectionError("The India Post window was closed before a result appeared.")):
        result = TrackingService.refresh_shipment(sid)
    assert result["status"] == "error"
    assert "window was closed" in result["error_message"]
