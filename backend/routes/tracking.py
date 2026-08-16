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
            error_msg_lower = error_msg.lower()
            clean_msg = error_msg.replace("NotImplementedError: ", "").replace("ValueError: ", "")
            
            if 'invalid tracking number' in error_msg_lower or 'valueerror' in error_msg_lower:
                logger.info("Returning INVALID_TRACKING_NUMBER")
                return jsonify({'success': False, 'error': {'code': 'INVALID_TRACKING_NUMBER', 'message': clean_msg}}), 422
            elif 'rate limit' in error_msg_lower or 'too many requests' in error_msg_lower or '429' in error_msg_lower:
                logger.info("Returning PROVIDER_RATE_LIMITED")
                return jsonify({'success': False, 'error': {'code': 'PROVIDER_RATE_LIMITED', 'message': clean_msg}}), 429
            elif 'timeout' in error_msg_lower:
                logger.info("Returning PROVIDER_TIMEOUT")
                return jsonify({'success': False, 'error': {'code': 'PROVIDER_TIMEOUT', 'message': clean_msg}}), 503
            elif any(term in error_msg_lower for term in ['network', 'connection refused', 'dns', 'unreachable', 'socket', 'connectionerror', 'requests.exceptions']):
                logger.info("Returning PROVIDER_NETWORK_ERROR")
                return jsonify({'success': False, 'error': {'code': 'PROVIDER_NETWORK_ERROR', 'message': clean_msg}}), 503
            elif 'notimplementederror' in error_msg_lower or 'authorized tracking integration' in error_msg_lower or 'provider unavailable' in error_msg_lower:
                logger.info("Returning PROVIDER_UNAVAILABLE")
                return jsonify({'success': False, 'error': {'code': 'PROVIDER_UNAVAILABLE', 'message': clean_msg}}), 503
            else:
                logger.info("Returning INTERNAL_ERROR for tracking failure")
                return jsonify({'success': False, 'error': {'code': 'INTERNAL_ERROR', 'message': 'Internal server error'}}), 500
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