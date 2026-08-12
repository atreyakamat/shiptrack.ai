from flask import Blueprint, jsonify, g, send_file
from backend.services.analytics_service import AnalyticsService
from backend.services.shipment_service import ShipmentService
from backend.utils.auth import token_required
import logging
import csv
import os
from tempfile import NamedTemporaryFile

logger = logging.getLogger(__name__)
analytics_bp = Blueprint('analytics', __name__)

@analytics_bp.route('/analytics', methods=['GET'])
@token_required
def get_analytics():
    try:
        overview = AnalyticsService.get_overview_stats(g.current_user.id)
        data = {
            'overview': overview,
            'delivery_rate': overview.get('delivery_rate', 0.0),
            'by_status': AnalyticsService.get_shipments_by_status(g.current_user.id)
        }
        return jsonify({'success': True, 'data': data}), 200
    except Exception as e:
        logger.error(f"Error getting analytics: {e}")
        return jsonify({'success': False, 'error': {'code': 'ANALYTICS_ERROR', 'message': 'Failed to fetch analytics'}}), 500

@analytics_bp.route('/analytics/overview', methods=['GET'])
@token_required
def get_overview():
    try:
        stats = AnalyticsService.get_overview_stats(g.current_user.id)
        return jsonify({'success': True, 'data': stats}), 200
    except Exception as e:
        logger.error(f"Error getting overview stats: {e}")
        return jsonify({'success': False, 'error': {'code': 'ANALYTICS_ERROR', 'message': 'Failed to fetch overview stats'}}), 500

@analytics_bp.route('/analytics/export', methods=['GET'])
@token_required
def export_csv():
    try:
        shipments = ShipmentService.get_all_shipments(g.current_user.id, {})
        temp = NamedTemporaryFile(mode='w', delete=False, suffix='.csv', newline='')
        writer = csv.writer(temp)
        writer.writerow(['Tracking Number', 'Carrier', 'Status', 'Origin', 'Destination', 'Category', 'Created At', 'Last Updated'])
        
        for s in shipments:
            writer.writerow([
                s.tracking_number, s.carrier, s.status, s.origin, s.destination, 
                s.category, s.created_at, s.last_updated
            ])
            
        temp.close()
        return send_file(temp.name, as_attachment=True, download_name='shiptrack_export.csv', mimetype='text/csv')
    except Exception as e:
        logger.error(f"Error exporting CSV: {e}")
        return jsonify({'success': False, 'error': {'code': 'ANALYTICS_ERROR', 'message': 'Failed to export CSV'}}), 500
