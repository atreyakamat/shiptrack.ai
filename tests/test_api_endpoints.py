import pytest
from backend.models.shipment import Shipment
from backend.extensions import db
from datetime import datetime, timezone

def test_health_check(client):
    rv = client.get('/api/health')
    assert rv.status_code == 200
    json_data = rv.get_json()
    assert json_data['status'] == 'ok'
    assert 'demo_mode' in json_data

def test_create_shipment(auth_client, app):
    rv = auth_client.post('/api/shipments', json={
        'tracking_number': 'EM111222333IN',
        'carrier': 'india_post',
        'description': 'Documents'
    })
    assert rv.status_code == 201
    json_data = rv.get_json()
    assert json_data['success'] is True
    assert json_data['data']['tracking_number'] == 'EM111222333IN'

    # Test duplicate 409
    rv2 = auth_client.post('/api/shipments', json={
        'tracking_number': 'EM111222333IN',
        'description': 'Test Shipment 2'
    })
    assert rv2.status_code == 409

    # Test invalid tracking number 400
    rv3 = auth_client.post('/api/shipments', json={
        'tracking_number': '12345',
        'description': 'Invalid'
    })
    assert rv3.status_code == 400

def test_get_shipments(auth_client, app, test_user):
    with app.app_context():
        s = Shipment(user_id=test_user.id, tracking_number='EM999999999IN', description='List me')
        db.session.add(s)
        db.session.commit()
        
    rv = auth_client.get('/api/shipments')
    assert rv.status_code == 200
    assert isinstance(rv.get_json()['data'], list)

def test_get_shipment_by_id(auth_client, app, test_user):
    with app.app_context():
        s = Shipment(user_id=test_user.id, tracking_number='EM888888888IN', description='Get me')
        db.session.add(s)
        db.session.commit()
        sid = s.id
        
    rv = auth_client.get(f'/api/shipments/{sid}')
    assert rv.status_code == 200
    assert rv.get_json()['data']['tracking_number'] == 'EM888888888IN'
    
    # Test 404
    rv_404 = auth_client.get('/api/shipments/999')
    assert rv_404.status_code == 404

def test_update_shipment(auth_client, app, test_user):
    with app.app_context():
        s = Shipment(user_id=test_user.id, tracking_number='EM777777777IN', description='Update me')
        db.session.add(s)
        db.session.commit()
        sid = s.id
        
    rv = auth_client.put(f'/api/shipments/{sid}', json={'description': 'Updated'})
    assert rv.status_code == 200
    assert rv.get_json()['data']['description'] == 'Updated'

def test_delete_shipment(auth_client, app, test_user):
    with app.app_context():
        s = Shipment(user_id=test_user.id, tracking_number='EM666666666IN', description='Delete me')
        db.session.add(s)
        db.session.commit()
        sid = s.id
        
    rv = auth_client.delete(f'/api/shipments/{sid}')
    assert rv.status_code == 200
    
    # Verify deleted
    rv2 = auth_client.get(f'/api/shipments/{sid}')
    assert rv2.status_code == 404

def test_refresh_shipment(auth_client, app, test_user):
    with app.app_context():
        # EM100000004IN is Delivered in the mock data
        s = Shipment(user_id=test_user.id, tracking_number='EM100000004IN', description='Refresh me')
        db.session.add(s)
        db.session.commit()
        sid = s.id
        
    rv = auth_client.post(f'/api/shipments/{sid}/refresh')
    assert rv.status_code == 200
    json_data = rv.get_json()
    assert json_data['data']['status'] == 'success'

def test_refresh_shipment_error(auth_client, app, test_user):
    with app.app_context():
        # EM100000007IN is configured to throw Tracking Error in mock data
        s = Shipment(user_id=test_user.id, tracking_number='EM100000007IN', description='Error me')
        db.session.add(s)
        db.session.commit()
        sid = s.id
        
    rv = auth_client.post(f'/api/shipments/{sid}/refresh')
    assert rv.status_code == 500
    assert 'error' in rv.get_json().get('status', '') or 'error' in rv.get_json()
