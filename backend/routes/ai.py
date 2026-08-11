from flask import Blueprint, jsonify, g
from backend.services.ai_service import AIService
from backend.services.shipment_service import ShipmentService
from backend.models.shipment import Shipment
from backend.models.ai_summary import AISummary
from backend.utils.auth import token_required
from backend.extensions import limiter
import logging

logger = logging.getLogger(__name__)
ai_bp = Blueprint('ai', __name__)

@ai_bp.route('/ai/<int:shipment_id>/summary', methods=['GET'])
@token_required
@limiter.limit("20 per minute")
def get_summary(shipment_id):
    try:
        summary = AISummary.query.filter_by(shipment_id=shipment_id, user_id=g.current_user.id).first()
        if summary:
            return jsonify({'success': True, 'data': summary.to_dict()}), 200
            
        shipment = ShipmentService.get_shipment(g.current_user.id, shipment_id)
        if not shipment:
            return jsonify({'success': False, 'error': {'code': 'NOT_FOUND', 'message': 'Shipment not found'}}), 404
            
        result = AIService.generate_summary(shipment)
        return jsonify({'success': True, 'data': result}), 200
    except Exception as e:
        logger.error(f"Error getting summary: {e}")
        return jsonify({'success': False, 'error': {'code': 'INTERNAL_ERROR', 'message': str(e)}}), 500

@ai_bp.route('/ai/<int:shipment_id>/generate', methods=['POST'])
@token_required
@limiter.limit("10 per minute")
def generate_summary(shipment_id):
    try:
        shipment = ShipmentService.get_shipment(g.current_user.id, shipment_id)
        if not shipment:
            return jsonify({'success': False, 'error': {'code': 'NOT_FOUND', 'message': 'Shipment not found'}}), 404
            
        result = AIService.generate_summary(shipment)
        return jsonify({'success': True, 'data': result}), 200
    except Exception as e:
        logger.error(f"Error generating summary: {e}")
        return jsonify({'success': False, 'error': {'code': 'INTERNAL_ERROR', 'message': str(e)}}), 500

@ai_bp.route('/ai/insights', methods=['GET', 'POST'])
@token_required
@limiter.limit("5 per minute")
def get_insights():
    try:
        shipments = Shipment.query.filter_by(user_id=g.current_user.id, is_archived=False).all()
        result = AIService.generate_insights(shipments)
        return jsonify({'success': True, 'data': result}), 200
    except Exception as e:
        logger.error(f"Error getting insights: {e}")
        return jsonify({'success': False, 'error': {'code': 'INTERNAL_ERROR', 'message': str(e)}}), 500
