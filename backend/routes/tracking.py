from flask import Blueprint, jsonify, g, request
from backend.services.tracking_service import TrackingService
from backend.services.shipment_service import ShipmentService
from backend.utils.auth import token_required
from backend.extensions import limiter
import logging

logger = logging.getLogger(__name__)
tracking_bp = Blueprint('tracking', __name__)

def _log_error(endpoint: str, error: Exception):
    logger.error(
        f"request_id={g.get('request_id', 'unknown')} "
        f"endpoint={endpoint} "
        f"method={request.method} "
        f"user_id={getattr(g.current_user, 'id', 'anonymous')} "
        f"error={type(error).__name__}: {error}"
    )

@tracking_bp.route('/shipments/<int:id>/refresh', methods=['POST'])
@token_required
@limiter.limit("10 per minute")
def refresh_shipment(id):
    try:
        # We verify shipment belongs to user first
        shipment = ShipmentService.get_shipment(g.current_user.id, id)
        if not shipment:
            return jsonify({'success': False, 'error': {'code': 'NOT_FOUND', 'message': 'Shipment not found'}}), 404
            
        result = TrackingService.refresh_shipment(id)
        logger.info(f"Tracking refresh result for {id}: {result}")
        if result.get('status') == 'error':
            error_msg = result.get('error_message', 'Unknown error')
            logger.info(f"Error message: {error_msg}")
            # Check if it's a provider unavailable error
            if 'NotImplementedError' in error_msg or 'authorized tracking integration' in error_msg:
                logger.info("Returning PROVIDER_UNAVAILABLE")
                return jsonify({'success': False, 'error': {'code': 'PROVIDER_UNAVAILABLE', 'message': 'Tracking provider is currently unavailable'}}), 503
            logger.info("Returning TRACKING_ERROR")
            return jsonify({'success': False, 'error': {'code': 'TRACKING_ERROR', 'message': 'Failed to refresh tracking'}}), 500
        return jsonify({'success': True, 'data': result}), 200
    except Exception as e:
        _log_error(f'/shipments/{id}/refresh POST', e)
        return jsonify({'success': False, 'error': {'code': 'INTERNAL_ERROR', 'message': 'Internal server error'}}), 500

@tracking_bp.route('/shipments/refresh-all', methods=['POST'])
@token_required
@limiter.limit("2 per minute")
def refresh_all():
    try:
        TrackingService.refresh_all_active(g.current_user.id)
        return jsonify({'success': True, 'message': 'Background refresh started'}), 202
    except Exception as e:
        _log_error('/shipments/refresh-all POST', e)
        return jsonify({'success': False, 'error': {'code': 'INTERNAL_ERROR', 'message': 'Internal server error'}}), 500

@tracking_bp.route('/shipments/<int:id>/history', methods=['GET'])
@token_required
def get_history(id):
    try:
        shipment = ShipmentService.get_shipment(g.current_user.id, id)
        if not shipment:
            return jsonify({'success': False, 'error': {'code': 'NOT_FOUND', 'message': 'Shipment not found'}}), 404
        return jsonify({'success': True, 'data': [e.to_dict() for e in shipment.tracking_events]}), 200
    except Exception as e:
        _log_error(f'/shipments/{id}/history GET', e)
        return jsonify({'success': False, 'error': {'code': 'INTERNAL_ERROR', 'message': 'Internal server error'}}), 500