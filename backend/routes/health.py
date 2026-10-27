from flask import Blueprint, jsonify, current_app

health_bp = Blueprint('health', __name__)

@health_bp.route('/health', methods=['GET'])
def health_check():
    cfg = current_app.config
    provider = cfg.get('TRACKING_PROVIDER', 'mock')
    demo = bool(cfg.get('TRACKING_DEMO_MODE', True)) or provider == 'mock'
    return jsonify({
        'status': 'ok',
        'version': '1.0.0',
        'demo_mode': demo,
        'tracking_provider': provider,
        'ai_provider': cfg.get('AI_PROVIDER', 'mock')
    }), 200
