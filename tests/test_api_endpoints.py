import pytest
from backend.models.shipment import Shipment
from backend.extensions import db
from datetime import datetime, timezone

def test_health_check(client):
    rv = client.get('/api/health')
    assert rv.status_code == 200
    json_data = rv.get_json()
    assert json_data['status'] == 'ok'
    assert json_data['demo_mode'] is True

def test_create_shipment(client, app):
    # Test valid 201
    rv = client.post('/api/shipments', json={
        'tracking_number': 'EE123456789IN',
        'description': 'Test Shipment'
    })
    assert rv.status_code == 201
    assert 'id' in rv.get_json()['data']

    # Test duplicate 409
    rv2 = client.post('/api/shipments', json={
        'tracking_number': 'EE123456789IN',
        'description': 'Test Shipment 2'
    })
    assert rv2.status_code == 409

    # Test invalid tracking number 400
    rv3 = client.post('/api/shipments', json={
        'tracking_number': '12345',
        'description': 'Invalid'
    })
    assert rv3.status_code == 400

def test_get_shipments(client, app):
    with app.app_context():
        s = Shipment(tracking_number='EM999999999IN', description='List me')
        db.session.add(s)
        db.session.commit()
        
    rv = client.get('/api/shipments')
    assert rv.status_code == 200
    assert isinstance(rv.get_json()['data'], list)

def test_get_shipment_by_id(client, app):
    with app.app_context():
        s = Shipment(tracking_number='EM888888888IN', description='Get me')
        db.session.add(s)
        db.session.commit()
        sid = s.id
        
    rv = client.get(f'/api/shipments/{sid}')
    assert rv.status_code == 200
    assert rv.get_json()['data']['tracking_number'] == 'EM888888888IN'
    
    # Test 404
    rv_404 = client.get('/api/shipments/999')
    assert rv_404.status_code == 404

def test_update_shipment(client, app):
    with app.app_context():
        s = Shipment(tracking_number='EM777777777IN', description='Update me')
        db.session.add(s)
        db.session.commit()
        sid = s.id
        
    rv = client.put(f'/api/shipments/{sid}', json={'description': 'Updated'})
    assert rv.status_code == 200
    assert rv.get_json()['data']['description'] == 'Updated'

def test_delete_shipment(client, app):
    with app.app_context():
        s = Shipment(tracking_number='EM666666666IN', description='Delete me')
        db.session.add(s)
        db.session.commit()
        sid = s.id
        
    rv = client.delete(f'/api/shipments/{sid}')
    assert rv.status_code == 200
    
    # Verify deleted
    rv2 = client.get(f'/api/shipments/{sid}')
    assert rv2.status_code == 404

def test_refresh_shipment(client, app):
    with app.app_context():
        # EM100000004IN is Delivered in the mock data
        s = Shipment(tracking_number='EM100000004IN', description='Refresh me')
        db.session.add(s)
        db.session.commit()
        sid = s.id
        
    rv = client.post(f'/api/shipments/{sid}/refresh')
    assert rv.status_code == 200
    json_data = rv.get_json()
    assert json_data['data']['status'] == 'success'

def test_refresh_shipment_error(client, app):
    with app.app_context():
        # EM100000007IN is configured to throw Tracking Error in mock data
        s = Shipment(tracking_number='EM100000007IN', description='Error me')
        db.session.add(s)
        db.session.commit()
        sid = s.id
        
    rv = client.post(f'/api/shipments/{sid}/refresh')
    assert rv.status_code == 500
    assert 'error' in rv.get_json().get('status', '') or 'error' in rv.get_json()
