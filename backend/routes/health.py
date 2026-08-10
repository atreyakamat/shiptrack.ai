from flask import Blueprint, jsonify
from backend.config import Config

health_bp = Blueprint('health', __name__)

@health_bp.route('/health', methods=['GET'])
def health_check():
    import os
    return jsonify({
        'status': 'ok',
        'version': '1.0.0',
        'demo_mode': os.getenv('TRACKING_DEMO_MODE', 'true').lower() == 'true',
        'tracking_provider': os.getenv('TRACKING_PROVIDER', 'mock'),
        'ai_provider': os.getenv('AI_PROVIDER', 'mock')
    }), 200
