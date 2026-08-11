import pytest
from backend.app import create_app
from backend.extensions import db
from backend.models.shipment import Shipment
from backend.models.tracking_event import TrackingEvent
from backend.models.user import User

@pytest.fixture
def app():
    app = create_app('testing')
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    
    with app.app_context():
        db.create_all()
        # Create a test user
        user = User(email="test@example.com")
        user.set_password("password")
        db.session.add(user)
        db.session.commit()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def auth_headers(client, app):
    res = client.post('/api/auth/login', json={'email': 'test@example.com', 'password': 'password'})
    token = res.json['data']['token']
    return {'Authorization': f'Bearer {token}'}

def test_api_success_envelope(client, auth_headers):
    res = client.get('/api/shipments', headers=auth_headers)
    assert res.status_code == 200
    data = res.json
    assert data['success'] is True
    assert 'data' in data
    assert isinstance(data['data'], list)

def test_api_error_envelope(client, auth_headers):
    res = client.get('/api/shipments/9999', headers=auth_headers)
    assert res.status_code == 404
    data = res.json
    assert data['success'] is False
    assert 'error' in data
    assert 'code' in data['error']
    assert 'message' in data['error']
    assert data['error']['code'] == 'NOT_FOUND'

def test_tracking_event_serialization(app):
    with app.app_context():
        event = TrackingEvent(
            shipment_id=1,
            status="Item Dispatched",
            location="Panaji H.O.",
            event_date="05/08/2026",
            event_time="12:15 PM"
        )
        d = event.to_dict()
        assert d['status'] == "Item Dispatched"
        assert d['location'] == "Panaji H.O."
        # Because we provided event_date and event_time, they should be merged to event_timestamp in ISO format
        assert d['event_timestamp'] == "2026-08-05T12:15:00"
        # The separated date/time keys should NOT be present
        assert 'event_date' not in d
        assert 'event_time' not in d

def test_shipment_serialization(app):
    with app.app_context():
        shipment = Shipment(
            user_id=1,
            tracking_number="EM123456789IN",
            carrier="india_post",
            description=None,
            origin=None
        )
        d = shipment.to_dict()
        assert d['tracking_number'] == "EM123456789IN"
        assert d['description'] is None
        assert d['origin'] is None
