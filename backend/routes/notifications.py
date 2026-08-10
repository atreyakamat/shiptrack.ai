from flask import Blueprint, jsonify, request, g
from backend.services.notification_service import NotificationService
from backend.models.notification_preference import NotificationPreference
from backend.extensions import db
from backend.utils.auth import token_required

notifications_bp = Blueprint('notifications', __name__)

@notifications_bp.route('/', methods=['GET'])
@token_required
def get_notifications():
    try:
        status = request.args.get('status')
        channel = request.args.get('channel')
        filters = {}
        if status:
            filters['status'] = status
        if channel:
            filters['channel'] = channel
            
        notifs = NotificationService.get_notifications(g.current_user.id, filters)
        return jsonify({'success': True, 'data': [n.to_dict() for n in notifs]}), 200
    except Exception as e:
        return jsonify({'success': False, 'error': {'code': 'INTERNAL_ERROR', 'message': 'Internal server error'}}), 500

@notifications_bp.route('/<int:id>/read', methods=['POST'])
@token_required
def mark_read(id):
    try:
        success = NotificationService.mark_as_read(g.current_user.id, id)
        if success:
            return jsonify({'success': True, 'data': {'status': 'success'}}), 200
        return jsonify({'success': False, 'error': {'code': 'NOT_FOUND', 'message': 'Notification not found'}}), 404
    except Exception as e:
        return jsonify({'success': False, 'error': {'code': 'INTERNAL_ERROR', 'message': 'Internal server error'}}), 500

@notifications_bp.route('/read-all', methods=['POST'])
@token_required
def mark_all_read():
    try:
        count = NotificationService.mark_all_as_read(g.current_user.id)
        return jsonify({'success': True, 'data': {'status': 'success', 'count': count}}), 200
    except Exception as e:
        return jsonify({'success': False, 'error': {'code': 'INTERNAL_ERROR', 'message': 'Internal server error'}}), 500

@notifications_bp.route('/preferences', methods=['GET'])
@token_required
def get_preferences():
    try:
        prefs = NotificationPreference.query.filter_by(user_id=g.current_user.id).all()
        return jsonify({'success': True, 'data': [p.to_dict() for p in prefs]}), 200
    except Exception as e:
        return jsonify({'success': False, 'error': {'code': 'INTERNAL_ERROR', 'message': 'Internal server error'}}), 500

@notifications_bp.route('/preferences/<event_type>', methods=['PUT'])
@token_required
def update_preference(event_type):
    try:
        data = request.json
        pref = NotificationPreference.query.filter_by(user_id=g.current_user.id, event_type=event_type).first()
        if not pref:
            return jsonify({'success': False, 'error': {'code': 'NOT_FOUND', 'message': 'Preference not found'}}), 404
            
        if 'in_app' in data:
            pref.in_app = data['in_app']
        if 'whatsapp' in data:
            pref.whatsapp = data['whatsapp']
        if 'email' in data:
            pref.email = data['email']
            
        db.session.commit()
        return jsonify({'success': True, 'data': pref.to_dict()}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': {'code': 'INTERNAL_ERROR', 'message': 'Internal server error'}}), 500
