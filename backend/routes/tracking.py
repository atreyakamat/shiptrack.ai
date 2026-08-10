from flask import Blueprint, jsonify
from backend.services.tracking_service import TrackingService
from backend.services.shipment_service import ShipmentService
from backend.utils.auth import token_required
from backend.extensions import limiter
import logging

logger = logging.getLogger(__name__)
tracking_bp = Blueprint('tracking', __name__)

@tracking_bp.route('/shipments/<int:id>/refresh', methods=['POST'])
@token_required
@limiter.limit("10 per minute")
def refresh_shipment(id):
    try:
        result = TrackingService.refresh_shipment(id)
        if result.get('status') == 'error':
            return jsonify({'success': False, 'error': {'code': 'REFRESH_ERROR', 'message': result.get('error_message', 'Unknown error')}}), 500
        return jsonify({'success': True, 'data': result}), 200
    except Exception as e:
        logger.error(f"Error refreshing shipment {id}: {e}")
        return jsonify({'success': False, 'error': {'code': 'INTERNAL_ERROR', 'message': 'Internal server error'}}), 500

@tracking_bp.route('/shipments/refresh-all', methods=['POST'])
@token_required
@limiter.limit("2 per minute")
def refresh_all():
    try:
        TrackingService.refresh_all_active()
        return jsonify({'success': True, 'message': 'Background refresh started'}), 202
    except Exception as e:
        logger.error(f"Error refreshing all: {e}")
        return jsonify({'success': False, 'error': {'code': 'INTERNAL_ERROR', 'message': 'Internal server error'}}), 500

@tracking_bp.route('/shipments/<int:id>/history', methods=['GET'])
@token_required
def get_history(id):
    try:
        shipment = ShipmentService.get_shipment(id)
        if not shipment:
            return jsonify({'success': False, 'error': {'code': 'NOT_FOUND', 'message': 'Shipment not found'}}), 404
        return jsonify({'success': True, 'data': [e.to_dict() for e in shipment.tracking_events]}), 200
    except Exception as e:
        logger.error(f"Error getting history for {id}: {e}")
        return jsonify({'success': False, 'error': {'code': 'INTERNAL_ERROR', 'message': 'Internal server error'}}), 500
