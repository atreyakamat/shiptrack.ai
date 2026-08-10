import pytest
import os
import sys
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from backend.app import create_app
from backend.extensions import db as _db
from backend.models import Shipment, TrackingEvent

@pytest.fixture
def app():
    app = create_app('testing')
    return app

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def db(app):
    with app.app_context():
        _db.create_all()
        yield _db
        _db.drop_all()

@pytest.fixture
def sample_shipment(db):
    shipment = Shipment(
        tracking_number='EM123456789IN',
        carrier='india_post',
        description='Test Shipment',
        status='IN_TRANSIT'
    )
    db.session.add(shipment)
    db.session.commit()
    return shipment

@pytest.fixture
def sample_tracking_events(db, sample_shipment):
    events = [
        TrackingEvent(shipment_id=sample_shipment.id, timestamp=datetime(2026, 1, 1), status='BOOKED', location='Goa', description='Booked'),
        TrackingEvent(shipment_id=sample_shipment.id, timestamp=datetime(2026, 1, 2), status='IN_TRANSIT', location='Mumbai', description='In Transit')
    ]
    db.session.add_all(events)
    db.session.commit()
    return events
