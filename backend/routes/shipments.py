from flask import Blueprint, request, jsonify, g
from backend.services.shipment_service import ShipmentService
from backend.utils.auth import token_required
from backend.extensions import limiter
import logging

logger = logging.getLogger(__name__)
shipments_bp = Blueprint('shipments', __name__)

def _log_error(endpoint: str, error: Exception):
    logger.error(
        f"request_id={g.get('request_id', 'unknown')} "
        f"endpoint={endpoint} "
        f"method={request.method} "
        f"user_id={getattr(g.current_user, 'id', 'anonymous')} "
        f"error={type(error).__name__}: {error}"
    )

@shipments_bp.route('/shipments', methods=['GET'])
@token_required
@limiter.limit("60 per minute")
def get_shipments():
    try:
        search = request.args.get('search')
        if search:
            shipments = ShipmentService.search_shipments(g.current_user.id, search)
        else:
            filters = {}
            if 'status' in request.args:
                filters['status'] = request.args.get('status')
            if 'carrier' in request.args:
                filters['carrier'] = request.args.get('carrier')
            shipments = ShipmentService.get_all_shipments(g.current_user.id, filters)
        
        return jsonify({'success': True, 'data': [s.to_dict() for s in shipments]}), 200
    except Exception as e:
        _log_error('/shipments GET', e)
        return jsonify({'success': False, 'error': {'code': 'INTERNAL_ERROR', 'message': 'Internal server error'}}), 500

@shipments_bp.route('/shipments', methods=['POST'])
@token_required
@limiter.limit("20 per minute")
def create_shipment():
    try:
        data = request.json
        shipment = ShipmentService.create_shipment(g.current_user.id, data)
        
        # Trigger initial refresh but decouple failure from shipment creation
        from backend.services.tracking_service import TrackingService
        try:
            TrackingService.refresh_shipment(shipment.id)
        except Exception as refresh_err:
            logger.warning(
                f"request_id={g.get('request_id', 'unknown')} "
                f"Initial tracking refresh failed for {shipment.id}, but shipment was saved: {refresh_err}"
            )
            
        return jsonify({'success': True, 'data': shipment.to_dict()}), 201
    except ValueError as ve:
        err_msg = str(ve)
        if "already exists" in err_msg.lower():
            return jsonify({'success': False, 'error': {'code': 'DUPLICATE_SHIPMENT', 'message': "This tracking number is already in your shipments."}}), 409
        return jsonify({'success': False, 'error': {'code': 'VALIDATION_ERROR', 'message': err_msg}}), 422
    except Exception as e:
        _log_error('/shipments POST', e)
        return jsonify({'success': False, 'error': {'code': 'INTERNAL_ERROR', 'message': 'Internal server error'}}), 500

@shipments_bp.route('/shipments/<int:id>', methods=['GET'])
@token_required
def get_shipment(id):
    try:
        shipment = ShipmentService.get_shipment(g.current_user.id, id)
        if not shipment:
            return jsonify({'success': False, 'error': {'code': 'NOT_FOUND', 'message': 'Shipment not found'}}), 404
            
        data = shipment.to_dict()
        data['events'] = [e.to_dict() for e in shipment.tracking_events]
        return jsonify({'success': True, 'data': data}), 200
    except Exception as e:
        _log_error(f'/shipments/{id} GET', e)
        return jsonify({'success': False, 'error': {'code': 'INTERNAL_ERROR', 'message': 'Internal server error'}}), 500

@shipments_bp.route('/shipments/<int:id>', methods=['PUT'])
@token_required
def update_shipment(id):
    try:
        data = request.json
        shipment = ShipmentService.update_shipment(g.current_user.id, id, data)
        if not shipment:
            return jsonify({'success': False, 'error': {'code': 'NOT_FOUND', 'message': 'Shipment not found'}}), 404
        return jsonify({'success': True, 'data': shipment.to_dict()}), 200
    except Exception as e:
        _log_error(f'/shipments/{id} PUT', e)
        return jsonify({'success': False, 'error': {'code': 'BAD_REQUEST', 'message': str(e)}}), 400

@shipments_bp.route('/shipments/<int:id>', methods=['DELETE'])
@token_required
def delete_shipment(id):
    try:
        success = ShipmentService.delete_shipment(g.current_user.id, id)
        if not success:
            return jsonify({'success': False, 'error': {'code': 'NOT_FOUND', 'message': 'Shipment not found'}}), 404
        return jsonify({'success': True, 'message': 'Shipment deleted'}), 200
    except Exception as e:
        _log_error(f'/shipments/{id} DELETE', e)
        return jsonify({'success': False, 'error': {'code': 'INTERNAL_ERROR', 'message': 'Internal server error'}}), 500

@shipments_bp.route('/shipments/<int:id>/archive', methods=['POST'])
@token_required
def archive_shipment(id):
    try:
        success = ShipmentService.archive_shipment(g.current_user.id, id)
        if not success:
            return jsonify({'success': False, 'error': {'code': 'NOT_FOUND', 'message': 'Shipment not found'}}), 404
        return jsonify({'success': True, 'message': 'Shipment archived'}), 200
    except Exception as e:
        _log_error(f'/shipments/{id}/archive POST', e)
        return jsonify({'success': False, 'error': {'code': 'INTERNAL_ERROR', 'message': 'Internal server error'}}), 500
