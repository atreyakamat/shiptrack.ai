import os
import sys
import pytest
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from backend.app import create_app
from backend.extensions import db as _db
from backend.models import User, Shipment, TrackingEvent, NotificationPreference

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
def users(db):
    from werkzeug.security import generate_password_hash
    user_a = User(email="usera@test.com", password_hash=generate_password_hash("pass_a"))
    user_b = User(email="userb@test.com", password_hash=generate_password_hash("pass_b"))
    db.session.add_all([user_a, user_b])
    db.session.commit()
    return user_a, user_b

@pytest.fixture
def shipments(db, users):
    user_a, user_b = users
    ship_a = Shipment(user_id=user_a.id, tracking_number="TRACK_A", carrier="mock", status="BOOKED")
    ship_b = Shipment(user_id=user_b.id, tracking_number="TRACK_B", carrier="mock", status="BOOKED")
    db.session.add_all([ship_a, ship_b])
    db.session.commit()
    return ship_a, ship_b

def get_token(client, email, password):
    res = client.post('/api/auth/login', json={'email': email, 'password': password})
    assert res.status_code == 200
    return res.json['data']['token']

def test_data_isolation(client, users, shipments):
    user_a, user_b = users
    ship_a, ship_b = shipments

    token_a = get_token(client, "usera@test.com", "pass_a")
    headers_a = {'Authorization': f'Bearer {token_a}'}

    # User A tries to read Shipment B
    res = client.get(f'/api/shipments/{ship_b.id}', headers=headers_a)
    assert res.status_code == 404, "User A should not find User B's shipment"

    # User A tries to edit Shipment B
    res = client.put(f'/api/shipments/{ship_b.id}', json={'description': 'Hacked'}, headers=headers_a)
    assert res.status_code == 404

    # User A tries to delete Shipment B
    res = client.delete(f'/api/shipments/{ship_b.id}', headers=headers_a)
    assert res.status_code == 404

    # User A tries to refresh Shipment B
    res = client.post(f'/api/tracking/{ship_b.id}/refresh', headers=headers_a)
    assert res.status_code == 404

    # User A tries to read User B's AI summary
    res = client.get(f'/api/ai/{ship_b.id}/summary', headers=headers_a)
    assert res.status_code == 404

    # Verify User A CAN read Shipment A
    res = client.get(f'/api/shipments/{ship_a.id}', headers=headers_a)
    assert res.status_code == 200

def test_authentication_tampering(client):
    # No token
    res = client.get('/api/shipments')
    assert res.status_code == 401

    # Malformed token
    res = client.get('/api/shipments', headers={'Authorization': 'Bearer NOT_A_REAL_TOKEN'})
    assert res.status_code == 401
