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
            
            if 'quota' in error_msg_lower:
                # Ship24 monthly quota spent — the UI offers the in-app CAPTCHA relay instead.
                logger.info("Returning PROVIDER_QUOTA")
                return jsonify({'success': False, 'error': {'code': 'PROVIDER_QUOTA', 'message': 'Ship24 monthly limit reached. Track this one with the in-app CAPTCHA instead.'}}), 429
            elif 'invalid tracking number' in error_msg_lower or 'valueerror' in error_msg_lower:
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

@tracking_bp.route('/tracking/captcha/start', methods=['POST'])
@token_required
@limiter.limit("20 per minute")
def captcha_start():
    """Open an India Post session and return the CAPTCHA image for the user to solve in-app."""
    try:
        data = request.json or {}
        tracking_number = (data.get('tracking_number') or '').strip().upper()
        if not tracking_number:
            return jsonify({'success': False, 'error': {'code': 'BAD_REQUEST', 'message': 'tracking_number is required'}}), 400
        from backend.carriers.india_post_captcha_manager import IndiaPostCaptchaManager
        result = IndiaPostCaptchaManager.instance().start_session(tracking_number, g.current_user.id)
        return jsonify({'success': True, 'data': result}), 200
    except ValueError as ve:
        return jsonify({'success': False, 'error': {'code': 'INVALID_TRACKING_NUMBER', 'message': str(ve)}}), 422
    except Exception as e:
        _log_error('/tracking/captcha/start POST', e)
        return jsonify({'success': False, 'error': {'code': 'PROVIDER_UNAVAILABLE', 'message': 'Could not reach India Post. Please try again.'}}), 503


@tracking_bp.route('/tracking/captcha/submit', methods=['POST'])
@token_required
@limiter.limit("30 per minute")
def captcha_submit():
    """Submit the human's CAPTCHA answer; on success, persist the result to the shipment."""
    try:
        data = request.json or {}
        session_id = data.get('session_id')
        answer = (data.get('answer') or '').strip()
        shipment_id = data.get('shipment_id')
        if not session_id or not answer:
            return jsonify({'success': False, 'error': {'code': 'BAD_REQUEST', 'message': 'session_id and answer are required'}}), 400

        from backend.carriers.india_post_captcha_manager import IndiaPostCaptchaManager
        outcome = IndiaPostCaptchaManager.instance().submit_answer(session_id, answer, g.current_user.id)

        status = outcome.get('status')
        if status == 'captcha_failed':
            return jsonify({'success': True, 'data': {'status': 'captcha_failed',
                            'captcha_image': outcome.get('captcha_image'), 'message': outcome.get('message')}}), 200
        if status == 'not_found':
            return jsonify({'success': False, 'error': {'code': 'NOT_FOUND', 'message': outcome.get('message')}}), 404
        if status == 'success':
            tracking_data = outcome['data']
            if shipment_id:
                shipment = ShipmentService.get_shipment(g.current_user.id, shipment_id)
                if not shipment:
                    return jsonify({'success': False, 'error': {'code': 'NOT_FOUND', 'message': 'Shipment not found'}}), 404
                TrackingService.persist_tracking_result(shipment_id, tracking_data)
                updated = ShipmentService.get_shipment(g.current_user.id, shipment_id)
                payload = updated.to_dict()
                payload['events'] = [e.to_dict() for e in updated.tracking_events]
                return jsonify({'success': True, 'data': {'status': 'success', 'shipment': payload}}), 200
            return jsonify({'success': True, 'data': {'status': 'success', 'tracking': tracking_data}}), 200

        return jsonify({'success': False, 'error': {'code': 'INTERNAL_ERROR', 'message': 'Unexpected tracking state'}}), 500
    except LookupError as le:
        return jsonify({'success': False, 'error': {'code': 'SESSION_EXPIRED', 'message': str(le)}}), 410
    except ValueError as ve:
        return jsonify({'success': False, 'error': {'code': 'BAD_REQUEST', 'message': str(ve)}}), 400
    except Exception as e:
        _log_error('/tracking/captcha/submit POST', e)
        return jsonify({'success': False, 'error': {'code': 'INTERNAL_ERROR', 'message': 'Could not complete tracking. Please try again.'}}), 500


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