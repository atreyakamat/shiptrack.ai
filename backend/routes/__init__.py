from flask import Blueprint

def register_routes(app):
    from .health import health_bp
    from .shipments import shipments_bp
    from .tracking import tracking_bp
    from .ocr import ocr_bp
    from .analytics import analytics_bp
    from .ai import ai_bp
    from .notifications import notifications_bp
    from .auth import auth_bp

    app.register_blueprint(health_bp, url_prefix='/api')
    app.register_blueprint(shipments_bp, url_prefix='/api')
    app.register_blueprint(tracking_bp, url_prefix='/api')
    app.register_blueprint(ocr_bp, url_prefix='/api')
    app.register_blueprint(analytics_bp, url_prefix='/api')
    app.register_blueprint(ai_bp, url_prefix='/api')
    app.register_blueprint(notifications_bp, url_prefix='/api/notifications')
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
