import os
import logging
from flask import Flask
from backend.config import config_map
from backend.extensions import db, cors, migrate
from backend.routes import register_routes
from backend.models import *

def create_app(config_name='default'):
    app = Flask(__name__)
    
    # Configuration
    app.config.from_object(config_map[config_name])
    
    # Configure logging
    log_level = getattr(logging, app.config.get('LOG_LEVEL', 'INFO').upper(), logging.INFO)
    logging.basicConfig(level=log_level, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # Init extensions
    db.init_app(app)
    cors.init_app(app)
    migrate.init_app(app, db)
    
    from backend.extensions import limiter
    limiter.init_app(app)
    
    # Create uploads directory
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    # Register blueprints
    register_routes(app)
    
    # Create tables
    with app.app_context():
        db.create_all()
        
    return app

def seed_db(app):
    with app.app_context():
        from backend.models.shipment import Shipment
        from backend.models.user import User
        from backend.services.shipment_service import ShipmentService
        from backend.services.tracking_service import TrackingService
        from backend.carriers.mock import MockCarrierAdapter
        from werkzeug.security import generate_password_hash

        admin_email = os.getenv('ADMIN_EMAIL')
        admin_password = os.getenv('ADMIN_PASSWORD')
        
        is_prod = os.getenv('FLASK_ENV', 'development') == 'production'
        if is_prod and admin_password == 'demo123':
            logger = logging.getLogger(__name__)
            logger.error("FATAL SECURITY ERROR: Insecure default password 'demo123' cannot be used in production.")
            sys.exit(1)

        if admin_email and admin_password:
            if User.query.filter_by(email=admin_email).first() is None:
                default_user = User(
                    email=admin_email,
                    password_hash=generate_password_hash(admin_password)
                )
                db.session.add(default_user)
                db.session.commit()
                
                # Optionally seed demo data if explicitly asked or if not in strict production
                if not is_prod or os.getenv('SEED_DEMO_DATA') == 'true':
                    adapter = MockCarrierAdapter()
                    for tracking_number in adapter.demo_data.keys():
                        shipment = ShipmentService.create_shipment(default_user.id, {
                            'tracking_number': tracking_number,
                            'carrier': 'mock',
                            'description': f'Demo shipment {tracking_number}'
                        })
                        TrackingService.refresh_shipment(shipment.id)
        elif not is_prod:
            # Fallback for local development ease if env vars not provided
            if User.query.filter_by(email="demo@shiptrack.ai").first() is None:
                default_user = User(
                    email="demo@shiptrack.ai",
                    password_hash=generate_password_hash("demo123")
                )
                db.session.add(default_user)
                db.session.commit()

if __name__ == '__main__':
    app = create_app()
    seed_db(app)
    app.run(debug=True, host='0.0.0.0', port=5000)
