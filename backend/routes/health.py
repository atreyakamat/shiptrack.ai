from flask import Blueprint, jsonify, current_app

health_bp = Blueprint('health', __name__)

@health_bp.route('/health', methods=['GET'])
def health_check():
    cfg = current_app.config
    provider = cfg.get('TRACKING_PROVIDER', 'mock')
    demo = bool(cfg.get('TRACKING_DEMO_MODE', True)) or provider == 'mock'
    # live_mode tells the UI how tracking works: demo (mock), web (in-app CAPTCHA),
    # or api (authorized aggregator, fully automatic).
    if demo:
        live_mode = 'demo'
    elif provider in ('web', 'india_post_web', 'human_assisted'):
        live_mode = 'web'
    else:
        live_mode = 'api'
    return jsonify({
        'status': 'ok',
        'version': '1.0.0',
        'demo_mode': demo,
        'live_mode': live_mode,
        'tracking_provider': provider,
        'ai_provider': cfg.get('AI_PROVIDER', 'mock')
    }), 200
