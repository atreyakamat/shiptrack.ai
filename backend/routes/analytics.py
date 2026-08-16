from flask import Blueprint, jsonify, g, send_file, request
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
            'by_status': AnalyticsService.get_shipments_by_status(g.current_user.id),
            'shipments_over_time': AnalyticsService.get_shipments_over_time(g.current_user.id),
            'delivery_time_distribution': AnalyticsService.get_delivery_time_distribution(g.current_user.id),
            'avg_delivery_by_carrier': AnalyticsService.get_avg_delivery_time_by_carrier(g.current_user.id),
            'avg_delivery_by_location': AnalyticsService.get_avg_delivery_time_by_location(g.current_user.id),
            'common_locations': AnalyticsService.get_common_locations(g.current_user.id),
            'stale_shipments': AnalyticsService.get_stale_shipments(g.current_user.id),
            'recent_activity': AnalyticsService.get_recent_activity(g.current_user.id)
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

@analytics_bp.route('/analytics/shipments-over-time', methods=['GET'])
@token_required
def get_shipments_over_time():
    try:
        months = int(request.args.get('months', 6))
        data = AnalyticsService.get_shipments_over_time(g.current_user.id, months)
        return jsonify({'success': True, 'data': data}), 200
    except Exception as e:
        logger.error(f"Error getting shipments over time: {e}")
        return jsonify({'success': False, 'error': {'code': 'ANALYTICS_ERROR', 'message': 'Failed to fetch shipments over time'}}), 500

@analytics_bp.route('/analytics/delivery-time-distribution', methods=['GET'])
@token_required
def get_delivery_time_distribution():
    try:
        data = AnalyticsService.get_delivery_time_distribution(g.current_user.id)
        return jsonify({'success': True, 'data': data}), 200
    except Exception as e:
        logger.error(f"Error getting delivery time distribution: {e}")
        return jsonify({'success': False, 'error': {'code': 'ANALYTICS_ERROR', 'message': 'Failed to fetch delivery time distribution'}}), 500

@analytics_bp.route('/analytics/delivery-by-carrier', methods=['GET'])
@token_required
def get_delivery_by_carrier():
    try:
        data = AnalyticsService.get_avg_delivery_time_by_carrier(g.current_user.id)
        return jsonify({'success': True, 'data': data}), 200
    except Exception as e:
        logger.error(f"Error getting delivery by carrier: {e}")
        return jsonify({'success': False, 'error': {'code': 'ANALYTICS_ERROR', 'message': 'Failed to fetch delivery by carrier'}}), 500

@analytics_bp.route('/analytics/delivery-by-location', methods=['GET'])
@token_required
def get_delivery_by_location():
    try:
        data = AnalyticsService.get_avg_delivery_time_by_location(g.current_user.id)
        return jsonify({'success': True, 'data': data}), 200
    except Exception as e:
        logger.error(f"Error getting delivery by location: {e}")
        return jsonify({'success': False, 'error': {'code': 'ANALYTICS_ERROR', 'message': 'Failed to fetch delivery by location'}}), 500

@analytics_bp.route('/analytics/stale-shipments', methods=['GET'])
@token_required
def get_stale_shipments():
    try:
        days = int(request.args.get('days', 7))
        data = AnalyticsService.get_stale_shipments(g.current_user.id, days)
        return jsonify({'success': True, 'data': data}), 200
    except Exception as e:
        logger.error(f"Error getting stale shipments: {e}")
        return jsonify({'success': False, 'error': {'code': 'ANALYTICS_ERROR', 'message': 'Failed to fetch stale shipments'}}), 500

@analytics_bp.route('/analytics/recent-activity', methods=['GET'])
@token_required
def get_recent_activity():
    try:
        limit = int(request.args.get('limit', 10))
        data = AnalyticsService.get_recent_activity(g.current_user.id, limit)
        return jsonify({'success': True, 'data': data}), 200
    except Exception as e:
        logger.error(f"Error getting recent activity: {e}")
        return jsonify({'success': False, 'error': {'code': 'ANALYTICS_ERROR', 'message': 'Failed to fetch recent activity'}}), 500

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
