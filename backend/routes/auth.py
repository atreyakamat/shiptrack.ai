from flask import Blueprint, request, jsonify, current_app
from backend.utils.auth import generate_token
from backend.extensions import limiter, db
from backend.models.user import User
from backend.models.notification_preference import NotificationPreference

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['POST'])
@limiter.limit("3 per minute")
def register():
    data = request.json
    email = data.get('email')
    password = data.get('password')
    
    if not email or not password:
        return jsonify({'success': False, 'error': {'code': 'BAD_REQUEST', 'message': 'Email and password are required'}}), 400
        
    if User.query.filter_by(email=email).first():
        return jsonify({'success': False, 'error': {'code': 'CONFLICT', 'message': 'Email already exists'}}), 409
        
    user = User(email=email)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    
    # Initialize default notification preferences for new user
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

@auth_bp.route('/login', methods=['POST'])
@limiter.limit("5 per minute")
def login():
    data = request.json
    email = data.get('email')
    password = data.get('password')
    
    if not email or not password:
        return jsonify({'success': False, 'error': {'code': 'BAD_REQUEST', 'message': 'Email and password are required'}}), 400
        
    user = User.query.filter_by(email=email).first()
    
    if user and user.check_password(password):
        token = generate_token(user.id)
        return jsonify({'success': True, 'data': {'token': token, 'user': user.to_dict()}}), 200
        
    return jsonify({'success': False, 'error': {'code': 'UNAUTHORIZED', 'message': 'Invalid credentials'}}), 401
