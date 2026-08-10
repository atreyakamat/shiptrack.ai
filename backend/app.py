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

def seed_db():
    from backend.models.shipment import Shipment
    from backend.services.shipment_service import ShipmentService
    from backend.services.tracking_service import TrackingService
    from backend.carriers.mock import MockCarrierAdapter

    if Shipment.query.count() == 0:
        adapter = MockCarrierAdapter()
        for tracking_number in adapter.demo_data.keys():
            shipment = ShipmentService.create_shipment({
                'tracking_number': tracking_number,
                'carrier': 'mock',
                'description': f'Demo shipment {tracking_number}'
            })
            TrackingService.refresh_shipment(shipment.id)

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5000)
