from flask import Blueprint, request, jsonify, current_app, g
from backend.utils.auth import generate_token
from backend.extensions import limiter, db
from backend.models.user import User
from backend.models.notification_preference import NotificationPreference
import logging

logger = logging.getLogger(__name__)
auth_bp = Blueprint('auth', __name__)

def _log_error(endpoint: str, error: Exception):
    logger.error(
        f"request_id={g.get('request_id', 'unknown')} "
        f"endpoint={endpoint} "
        f"method={request.method} "
        f"error={type(error).__name__}: {error}"
    )

@auth_bp.route('/register', methods=['POST'])
@limiter.limit("3 per minute")
def register():
    try:
        data = request.json
        email = data.get('email')
        
        if not email:
            return jsonify({'success': False, 'error': {'code': 'BAD_REQUEST', 'message': 'Email is required'}}), 400
            
        if User.query.filter_by(email=email).first():
            return jsonify({'success': False, 'error': {'code': 'CONFLICT', 'message': 'Email already exists'}}), 409
            
        password = data.get('password')
        if not password:
            return jsonify({'success': False, 'error': {'code': 'BAD_REQUEST', 'message': 'Password is required'}}), 400
            
        user = User(email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        
        default_prefs = [
            NotificationPreference(user_id=user.id, event_type='SHIPMENT_ADDED', in_app=True),
            NotificationPreference(user_id=user.id, event_type='STATUS_CHANGED', in_app=True),
            NotificationPreference(user_id=user.id, event_type='OUT_FOR_DELIVERY', in_app=True, whatsapp=True),
            NotificationPreference(user_id=user.id, event_type='DELIVERED', in_app=True, whatsapp=True),
            NotificationPreference(user_id=user.id, event_type='DELAYED', in_app=True, email=True),
            NotificationPreference(user_id=user.id, event_type='REFRESH_FAILED', in_app=True)
        ]
        db.session.bulk_save_objects(default_prefs)
        db.session.commit()
        
        token = generate_token(user.id)
        return jsonify({'success': True, 'data': {'token': token, 'user': user.to_dict()}}), 201
    except Exception as e:
        _log_error('/auth/register POST', e)
        db.session.rollback()
        return jsonify({'success': False, 'error': {'code': 'INTERNAL_ERROR', 'message': 'Internal server error'}}), 500

@auth_bp.route('/login', methods=['POST'])
@limiter.limit("5 per minute")
def login():
    try:
        data = request.json
        email = data.get('email')
        
        if not email:
            return jsonify({'success': False, 'error': {'code': 'BAD_REQUEST', 'message': 'Email is required'}}), 400
            
        password = data.get('password')
        if not password:
            return jsonify({'success': False, 'error': {'code': 'BAD_REQUEST', 'message': 'Password is required'}}), 400
            
        user = User.query.filter_by(email=email).first()
        if not user or not user.check_password(password):
            return jsonify({'success': False, 'error': {'code': 'UNAUTHORIZED', 'message': 'Invalid credentials'}}), 401
        
        token = generate_token(user.id)
        return jsonify({'success': True, 'data': {'token': token, 'user': user.to_dict()}}), 200
    except Exception as e:
        _log_error('/auth/login POST', e)
        db.session.rollback()
        return jsonify({'success': False, 'error': {'code': 'INTERNAL_ERROR', 'message': 'Internal server error'}}), 500
