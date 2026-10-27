#!/bin/sh
set -e
# Create tables and (in demo mode) seed the demo account + sample shipments.
python -c "from backend.app import create_app, seed_db; app = create_app('production'); seed_db(app)" || echo "[entrypoint] seed step skipped"
exec gunicorn --bind 0.0.0.0:5000 --workers 2 --timeout 120 "backend.app:create_app('production')"
