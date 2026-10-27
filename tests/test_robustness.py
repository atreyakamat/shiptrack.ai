"""Tests for the robustness hardening: secret guard, input validation, CSV streaming."""
import pytest
from backend.app import create_app


def test_production_rejects_insecure_secret(monkeypatch):
    from backend.config import ProductionConfig
    monkeypatch.setattr(ProductionConfig, 'SECRET_KEY', 'change-me-in-production')
    with pytest.raises(RuntimeError, match='SECRET_KEY'):
        create_app('production')


def test_register_rejects_invalid_email(client, db):
    res = client.post('/api/auth/register', json={'email': 'not-an-email', 'password': 'longenough1'})
    assert res.status_code == 400
    assert res.json['error']['code'] == 'BAD_REQUEST'


def test_register_rejects_short_password(client, db):
    res = client.post('/api/auth/register', json={'email': 'ok@shiptrack.ai', 'password': 'short'})
    assert res.status_code == 400


def test_register_accepts_valid_credentials(client, db):
    res = client.post('/api/auth/register', json={'email': 'new@shiptrack.ai', 'password': 'longenough1'})
    assert res.status_code == 201
    assert res.json['data']['token']


def test_login_missing_body_is_400_not_500(client, db):
    res = client.post('/api/auth/login', json={})
    assert res.status_code == 400


def test_csv_export_streams_as_csv(auth_client, sample_shipment):
    res = auth_client.get('/api/analytics/export')
    assert res.status_code == 200
    assert 'text/csv' in res.content_type
    assert 'attachment' in res.headers.get('Content-Disposition', '')
    assert b'Tracking Number' in res.data


def test_validators_email_and_password():
    from backend.utils.validators import validate_email, validate_password
    assert validate_email('a@b.com') is True
    assert validate_email('bad') is False
    assert validate_email('') is False
    assert validate_password('12345678') is True
    assert validate_password('short') is False
