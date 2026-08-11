#!/usr/bin/env python3
"""ShipTrack AI - Backend Server Entry Point"""
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(__file__))

from backend.app import create_app, seed_db

app = create_app()
seed_db(app)

if __name__ == '__main__':
    port = int(os.getenv('FLASK_RUN_PORT', '5000'))
    debug = os.getenv('FLASK_ENV', 'development') == 'development'
    print(f'\n  ShipTrack AI Backend')
    print(f'  Running on http://localhost:{port}')
    print(f'  Debug mode: {debug}')
    print(f'  Demo mode: {app.config.get("TRACKING_DEMO_MODE", True)}\n')
    app.run(host='0.0.0.0', port=port, debug=debug)
