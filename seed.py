"""
Seed script for ShipTrack AI database.
Creates realistic demo shipments with India Post tracking events.
"""
import os
import sys
from datetime import datetime, timezone

# Add project root to path
sys.path.insert(0, os.path.dirname(__file__))

from backend.app import create_app
from backend.extensions import db
from backend.models import Shipment, TrackingEvent, Notification, AISummary, RefreshLog, NotificationPreference

app = create_app()


def seed_db():
    with app.app_context():
        # Create tables
        db.create_all()

        # Check if data already exists
        if Shipment.query.first():
            print("\033[93m[!] Database already seeded. Skipping.\033[0m")
            return

        print("\033[94m[*] Seeding ShipTrack AI database with demo data...\033[0m\n")

        # ── Shipment 1: OUT_FOR_DELIVERY ─────────────────────────
        s1 = Shipment(
            tracking_number="EM740043207IN",
            carrier="india_post",
            description="Passport Application Documents",
            category="documents",
            origin="Bicholim Industrial Estate S.O, Goa 403504",
            destination="Bambavada S.O, Goa 403107",
            current_location="Bambavada S.O",
            priority="high",
            status="OUT_FOR_DELIVERY",
            article_type="Speed Post",
            origin_pincode="403504",
            destination_pincode="403107",
            booked_at=datetime(2026, 8, 5, 12, 15),
            last_updated=datetime(2026, 8, 7, 14, 15),
        )
        db.session.add(s1)
        db.session.flush()

        events1 = [
            TrackingEvent(shipment_id=s1.id, event_date="05/08/2026", event_time="12:15 PM",
                          status="BOOKED", location="Bicholim Industrial Estate S.O",
                          description="Item Booked", raw_status="Item Booked"),
            TrackingEvent(shipment_id=s1.id, event_date="05/08/2026", event_time="01:39 PM",
                          status="DISPATCHED", location="Bicholim Industrial Estate S.O",
                          description="Item Bagged", raw_status="Item Bagged"),
            TrackingEvent(shipment_id=s1.id, event_date="05/08/2026", event_time="06:50 PM",
                          status="IN_TRANSIT", location="Panaji NSH",
                          description="Bag Received", raw_status="Bag Received"),
            TrackingEvent(shipment_id=s1.id, event_date="05/08/2026", event_time="08:15 PM",
                          status="DISPATCHED", location="Panaji NSH",
                          description="Item Dispatched", raw_status="Item Dispatched"),
            TrackingEvent(shipment_id=s1.id, event_date="06/08/2026", event_time="04:30 AM",
                          status="IN_TRANSIT", location="Kolhapur Division",
                          description="Bag Received", raw_status="Bag Received"),
            TrackingEvent(shipment_id=s1.id, event_date="06/08/2026", event_time="11:00 AM",
                          status="IN_TRANSIT", location="Margao HO",
                          description="Item Received", raw_status="Item Received"),
            TrackingEvent(shipment_id=s1.id, event_date="07/08/2026", event_time="09:30 AM",
                          status="IN_TRANSIT", location="Bambavada S.O",
                          description="Item received at Destination", raw_status="Item received at Destination"),
            TrackingEvent(shipment_id=s1.id, event_date="07/08/2026", event_time="02:15 PM",
                          status="OUT_FOR_DELIVERY", location="Bambavada S.O",
                          description="Taken out for delivery", raw_status="Taken out for delivery"),
        ]
        db.session.add_all(events1)
        print("  [+] Shipment 1: EM740043207IN (OUT_FOR_DELIVERY)")

        # ── Shipment 2: DELIVERED ────────────────────────────────
        s2 = Shipment(
            tracking_number="EE123456789IN",
            carrier="india_post",
            description="Online Shopping - Electronics",
            category="package",
            origin="Mapusa HO, Goa",
            destination="Andheri East, Mumbai 400069",
            current_location="Andheri East",
            priority="normal",
            status="DELIVERED",
            article_type="Registered Parcel",
            booked_at=datetime(2026, 8, 1, 10, 0),
            last_updated=datetime(2026, 8, 3, 11, 30),
        )
        db.session.add(s2)
        db.session.flush()

        events2 = [
            TrackingEvent(shipment_id=s2.id, event_date="01/08/2026", event_time="10:00 AM",
                          status="BOOKED", location="Mapusa HO",
                          description="Item Booked", raw_status="Item Booked"),
            TrackingEvent(shipment_id=s2.id, event_date="01/08/2026", event_time="02:30 PM",
                          status="DISPATCHED", location="Mapusa HO",
                          description="Item Bagged", raw_status="Item Bagged"),
            TrackingEvent(shipment_id=s2.id, event_date="01/08/2026", event_time="06:00 PM",
                          status="IN_TRANSIT", location="Panaji NSH",
                          description="Bag Received", raw_status="Bag Received"),
            TrackingEvent(shipment_id=s2.id, event_date="02/08/2026", event_time="03:00 AM",
                          status="DISPATCHED", location="Panaji NSH",
                          description="Item Dispatched", raw_status="Item Dispatched"),
            TrackingEvent(shipment_id=s2.id, event_date="02/08/2026", event_time="11:00 AM",
                          status="IN_TRANSIT", location="Mumbai GPO",
                          description="Bag Received", raw_status="Bag Received"),
            TrackingEvent(shipment_id=s2.id, event_date="02/08/2026", event_time="04:00 PM",
                          status="IN_TRANSIT", location="Andheri East DO",
                          description="Item Received", raw_status="Item Received"),
            TrackingEvent(shipment_id=s2.id, event_date="03/08/2026", event_time="08:00 AM",
                          status="OUT_FOR_DELIVERY", location="Andheri East DO",
                          description="Taken out for delivery", raw_status="Taken out for delivery"),
            TrackingEvent(shipment_id=s2.id, event_date="03/08/2026", event_time="11:30 AM",
                          status="DELIVERED", location="Andheri East",
                          description="Item Delivered", raw_status="Item Delivered"),
        ]
        db.session.add_all(events2)
        print("  [+] Shipment 2: EE123456789IN (DELIVERED)")

        # ── Shipment 3: IN_TRANSIT ───────────────────────────────
        s3 = Shipment(
            tracking_number="RM987654321IN",
            carrier="india_post",
            description="Legal Documents - Court Filing",
            category="legal",
            origin="Ponda HO, Goa",
            destination="New Delhi GPO",
            current_location="Mumbai Transit",
            priority="urgent",
            status="IN_TRANSIT",
            article_type="Registered Letter",
            booked_at=datetime(2026, 8, 8, 9, 0),
            last_updated=datetime(2026, 8, 9, 20, 0),
        )
        db.session.add(s3)
        db.session.flush()

        events3 = [
            TrackingEvent(shipment_id=s3.id, event_date="08/08/2026", event_time="09:00 AM",
                          status="BOOKED", location="Ponda HO",
                          description="Item Booked", raw_status="Item Booked"),
            TrackingEvent(shipment_id=s3.id, event_date="08/08/2026", event_time="11:30 AM",
                          status="DISPATCHED", location="Ponda HO",
                          description="Item Bagged", raw_status="Item Bagged"),
            TrackingEvent(shipment_id=s3.id, event_date="08/08/2026", event_time="05:00 PM",
                          status="IN_TRANSIT", location="Panaji NSH",
                          description="Bag Received", raw_status="Bag Received"),
            TrackingEvent(shipment_id=s3.id, event_date="09/08/2026", event_time="02:00 AM",
                          status="DISPATCHED", location="Panaji NSH",
                          description="Item Dispatched", raw_status="Item Dispatched"),
            TrackingEvent(shipment_id=s3.id, event_date="09/08/2026", event_time="08:00 PM",
                          status="IN_TRANSIT", location="Mumbai Transit",
                          description="Bag Received", raw_status="Bag Received"),
        ]
        db.session.add_all(events3)
        print("  [+] Shipment 3: RM987654321IN (IN_TRANSIT)")

        # ── Shipment 4: BOOKED ───────────────────────────────────
        s4 = Shipment(
            tracking_number="EP111222333IN",
            carrier="india_post",
            description="Business Stickers Order #1547",
            category="business",
            origin="Margao HO, Goa",
            destination="Pune GPO",
            current_location="Margao HO",
            priority="normal",
            status="BOOKED",
            article_type="Speed Post",
            booked_at=datetime(2026, 8, 10, 10, 30),
            last_updated=datetime(2026, 8, 10, 10, 30),
        )
        db.session.add(s4)
        db.session.flush()

        events4 = [
            TrackingEvent(shipment_id=s4.id, event_date="10/08/2026", event_time="10:30 AM",
                          status="BOOKED", location="Margao HO",
                          description="Item Booked", raw_status="Item Booked"),
        ]
        db.session.add_all(events4)
        print("  [+] Shipment 4: EP111222333IN (BOOKED)")

        # ── Shipment 5: DELIVERED (older) ────────────────────────
        s5 = Shipment(
            tracking_number="EC555666777IN",
            carrier="india_post",
            description="University Certificate",
            category="documents",
            origin="Vasco Da Gama HO, Goa",
            destination="Bangalore GPO",
            current_location="Bangalore Koramangala",
            priority="normal",
            status="DELIVERED",
            article_type="Registered Parcel",
            booked_at=datetime(2026, 7, 20, 11, 0),
            last_updated=datetime(2026, 7, 22, 17, 30),
        )
        db.session.add(s5)
        db.session.flush()

        events5 = [
            TrackingEvent(shipment_id=s5.id, event_date="20/07/2026", event_time="11:00 AM",
                          status="BOOKED", location="Vasco Da Gama HO",
                          description="Item Booked", raw_status="Item Booked"),
            TrackingEvent(shipment_id=s5.id, event_date="20/07/2026", event_time="02:00 PM",
                          status="DISPATCHED", location="Vasco Da Gama HO",
                          description="Item Bagged", raw_status="Item Bagged"),
            TrackingEvent(shipment_id=s5.id, event_date="20/07/2026", event_time="07:00 PM",
                          status="IN_TRANSIT", location="Panaji NSH",
                          description="Bag Received", raw_status="Bag Received"),
            TrackingEvent(shipment_id=s5.id, event_date="21/07/2026", event_time="01:00 AM",
                          status="DISPATCHED", location="Panaji NSH",
                          description="Item Dispatched", raw_status="Item Dispatched"),
            TrackingEvent(shipment_id=s5.id, event_date="21/07/2026", event_time="06:00 PM",
                          status="IN_TRANSIT", location="Hubli Transit",
                          description="Bag Received", raw_status="Bag Received"),
            TrackingEvent(shipment_id=s5.id, event_date="22/07/2026", event_time="10:00 AM",
                          status="IN_TRANSIT", location="Bangalore GPO",
                          description="Item Received", raw_status="Item Received"),
            TrackingEvent(shipment_id=s5.id, event_date="22/07/2026", event_time="02:00 PM",
                          status="OUT_FOR_DELIVERY", location="Bangalore Koramangala DO",
                          description="Taken out for delivery", raw_status="Taken out for delivery"),
            TrackingEvent(shipment_id=s5.id, event_date="22/07/2026", event_time="05:30 PM",
                          status="DELIVERED", location="Bangalore Koramangala",
                          description="Item Delivered", raw_status="Item Delivered"),
        ]
        db.session.add_all(events5)
        print("  [+] Shipment 5: EC555666777IN (DELIVERED)")

        # ── Notifications ────────────────────────────────────────
        now = datetime.now(timezone.utc)
        n1 = Notification(
            shipment_id=s1.id,
            channel="in_app",
            notification_type="status_change",
            message="EM740043207IN is now Out for Delivery at Bambavada S.O.",
            status="unread",
            created_at=now,
        )
        n2 = Notification(
            shipment_id=s2.id,
            channel="in_app",
            notification_type="delivered",
            message="EE123456789IN has been delivered at Andheri East.",
            status="unread",
            created_at=now,
        )
        n3 = Notification(
            shipment_id=s3.id,
            channel="in_app",
            notification_type="delay_warning",
            message="RM987654321IN has not received a new scan for 24 hours.",
            status="unread",
            created_at=now,
        )
        db.session.add_all([n1, n2, n3])
        print("  [+] 3 Notifications created")

        # ── Notification Preferences ─────────────────────────────
        p1 = NotificationPreference(event_type="SHIPMENT_ADDED", in_app=True, whatsapp=False, email=False)
        p2 = NotificationPreference(event_type="STATUS_CHANGED", in_app=True, whatsapp=True, email=False)
        p3 = NotificationPreference(event_type="OUT_FOR_DELIVERY", in_app=True, whatsapp=True, email=False)
        p4 = NotificationPreference(event_type="DELIVERED", in_app=True, whatsapp=True, email=False)
        p5 = NotificationPreference(event_type="DELAYED", in_app=True, whatsapp=True, email=True)
        p6 = NotificationPreference(event_type="REFRESH_FAILED", in_app=True, whatsapp=False, email=False)
        
        db.session.add_all([p1, p2, p3, p4, p5, p6])
        print("  [+] 6 Notification Preferences created")

        # ── AI Summaries ─────────────────────────────────────────
        a1 = AISummary(
            shipment_id=s1.id,
            summary="The shipment has reached the destination delivery office at Bambavada S.O and is currently out for delivery. Based on the tracking pattern, delivery is expected today. The package traveled through Panaji NSH, Kolhapur Division, and Margao HO before arriving at the destination.",
            delay_analysis="No significant delays detected. Transit time is within normal range for this route.",
            prediction="Delivery expected today (07/08/2026).",
            health_status="NORMAL",
            model="mock",
        )
        a2 = AISummary(
            shipment_id=s2.id,
            summary="The shipment was successfully delivered on 03/08/2026 at Andheri East, Mumbai. Total transit time was approximately 2 days from booking to delivery, which is within the expected Speed Post delivery window for Goa to Mumbai route.",
            delay_analysis="No delays were detected during transit.",
            prediction="Delivered.",
            health_status="DELIVERED",
            model="mock",
        )
        db.session.add_all([a1, a2])
        print("  [+] 2 AI Summaries created")

        # ── Refresh Logs ─────────────────────────────────────────
        r1 = RefreshLog(
            shipment_id=s1.id,
            started_at=now,
            completed_at=now,
            status="success",
            events_found=8,
        )
        r2 = RefreshLog(
            shipment_id=s3.id,
            started_at=now,
            completed_at=now,
            status="success",
            events_found=5,
        )
        db.session.add_all([r1, r2])
        print("  [+] 2 Refresh Logs created")

        db.session.commit()
        print("\n\033[92m[OK] Successfully seeded database with 5 shipments, 30 events, 3 notifications, 2 AI summaries, and 2 refresh logs.\033[0m")


if __name__ == '__main__':
    seed_db()
