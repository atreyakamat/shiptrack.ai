import os
import sys
import time
import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from backend.app import create_app
from backend.services.shipment_service import ShipmentService
from backend.services.tracking_service import TrackingService
from backend.config import config_map

# Initialize logging for the scheduler
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('scheduler')

def refresh_shipments_job(app):
    with app.app_context():
        logger.info("Starting background refresh job...")
        try:
            # We don't filter by user_id here; we want to refresh ALL active shipments globally
            shipments_to_refresh = ShipmentService.get_shipments_needing_refresh()
            logger.info(f"Found {len(shipments_to_refresh)} shipments needing refresh.")
            
            for shipment in shipments_to_refresh:
                try:
                    TrackingService.refresh_shipment(shipment.id)
                    time.sleep(1) # Add a tiny delay between requests to not overload the API completely
                except Exception as e:
                    logger.error(f"Error refreshing shipment {shipment.id}: {e}")
            logger.info("Finished background refresh job.")
        except Exception as e:
            logger.error(f"Failed to fetch shipments for refresh: {e}")

def run_scheduler():
    config_name = os.getenv('FLASK_ENV', 'default')
    app = create_app(config_name)
    
    if not app.config.get('SCHEDULER_ENABLED', False):
        logger.info("Scheduler is disabled in configuration. Exiting.")
        return

    interval_minutes = int(app.config.get('REFRESH_INTERVAL_MINUTES', 60))
    logger.info(f"Starting scheduler. Refresh interval: {interval_minutes} minutes.")

    scheduler = BackgroundScheduler()
    # Adding jitter to prevent exact simultaneous execution if restarted
    trigger = IntervalTrigger(minutes=interval_minutes, jitter=60)
    scheduler.add_job(
        func=refresh_shipments_job,
        trigger=trigger,
        args=[app],
        id='refresh_shipments',
        name='Refresh all active shipments',
        replace_existing=True
    )
    
    scheduler.start()
    
    try:
        # Keep the main thread alive since BackgroundScheduler is in a daemon thread
        while True:
            time.sleep(60)
    except (KeyboardInterrupt, SystemExit):
        logger.info("Scheduler shutting down...")
        scheduler.shutdown()

if __name__ == '__main__':
    run_scheduler()
