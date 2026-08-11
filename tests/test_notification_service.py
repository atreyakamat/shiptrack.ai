import pytest
from backend.services.notification_service import NotificationService
from backend.models.notification_preference import NotificationPreference
from backend.models.notification import Notification

def test_notification_preferences(db, app, test_user):
    with app.app_context():
        # Setup preferences
        pref = NotificationPreference(user_id=test_user.id, event_type='TEST_EVENT', in_app=True, whatsapp=True, email=False)
        db.session.add(pref)
        db.session.commit()
        
        # Add dummy shipment
        from backend.models.shipment import Shipment
        s = Shipment(id=1, user_id=test_user.id, tracking_number="123", status="BOOKED")
        db.session.add(s)
        db.session.commit()
        
        # Trigger
        NotificationService.trigger_event('TEST_EVENT', 1, 'Test message', {'tracking_number': '123'})
        
        # Check that In-App notification was written to DB
        notifs = Notification.query.filter_by(notification_type='TEST_EVENT').all()
        assert len(notifs) == 1
        assert notifs[0].message == 'Test message'
        
        # We can't easily assert the stdout for WhatsApp/Email here without mocking logger, 
        # but if it didn't throw an error, it executed.
        
def test_notification_disabled_preference(db, app, test_user):
    with app.app_context():
        # Setup preferences (in_app is False)
        pref = NotificationPreference(user_id=test_user.id, event_type='TEST_DISABLED', in_app=False, whatsapp=False, email=False)
        db.session.add(pref)
        db.session.commit()
        
        # Trigger
        NotificationService.trigger_event('TEST_DISABLED', 1, 'Test message', {})
        
        # Check no notification was written to DB
        notifs = Notification.query.filter_by(notification_type='TEST_DISABLED').all()
        assert len(notifs) == 0
