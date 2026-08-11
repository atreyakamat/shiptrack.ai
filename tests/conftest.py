import pytest
import os
import sys
from datetime import datetime
from werkzeug.security import generate_password_hash

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from backend.app import create_app
from backend.extensions import db as _db
from backend.models import Shipment, TrackingEvent, User

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
def test_user(db):
    user = User(email="test@shiptrack.ai", password_hash=generate_password_hash("test1234"))
    db.session.add(user)
    db.session.commit()
    return user

@pytest.fixture
def auth_client(client, test_user):
    res = client.post('/api/auth/login', json={'email': 'test@shiptrack.ai', 'password': 'test1234'})
    token = res.json['data']['token']
    client.environ_base['HTTP_AUTHORIZATION'] = f'Bearer {token}'
    return client

@pytest.fixture
def sample_shipment(db, test_user):
    shipment = Shipment(
        user_id=test_user.id,
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
        TrackingEvent(shipment_id=sample_shipment.id, event_date="01-01-2026", event_time="10:00:00", status='BOOKED', location='Goa', description='Booked'),
        TrackingEvent(shipment_id=sample_shipment.id, event_date="02-01-2026", event_time="11:00:00", status='IN_TRANSIT', location='Mumbai', description='In Transit')
    ]
    db.session.add_all(events)
    db.session.commit()
    return events
