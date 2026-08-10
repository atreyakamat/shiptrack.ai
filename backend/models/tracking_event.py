from datetime import datetime, timezone
from backend.extensions import db

class TrackingEvent(db.Model):
    __tablename__ = 'tracking_event'

    id = db.Column(db.Integer, primary_key=True)
    shipment_id = db.Column(db.Integer, db.ForeignKey('shipment.id'), nullable=False)
    event_date = db.Column(db.String(20))
    event_time = db.Column(db.String(20))
    status = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(200))
    description = db.Column(db.String(500))
    raw_status = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        db.Index('idx_event_dedup', 'shipment_id', 'event_date', 'event_time', 'status', 'location'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'shipment_id': self.shipment_id,
            'event_date': self.event_date,
            'event_time': self.event_time,
            'status': self.status,
            'location': self.location,
            'description': self.description,
            'raw_status': self.raw_status,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
