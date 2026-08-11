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
    location_code = db.Column(db.String(50))
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    description = db.Column(db.String(500))
    raw_status = db.Column(db.String(200))
    source = db.Column(db.String(50))
    event_timestamp = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        db.Index('idx_event_dedup', 'shipment_id', 'event_date', 'event_time', 'status', 'location'),
    )

    def to_dict(self):
        # Derive timestamp if missing
        timestamp = None
        if self.event_timestamp:
            timestamp = self.event_timestamp.isoformat()
        elif self.event_date:
            ts_str = self.event_date
            if self.event_time:
                ts_str += f"T{self.event_time}"
            timestamp = ts_str
            
        return {
            'id': self.id,
            'shipment_id': self.shipment_id,
            'status': self.status,
            'location': self.location,
            'location_code': self.location_code,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'description': self.description,
            'raw_status': self.raw_status,
            'source': self.source,
            'event_timestamp': timestamp,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
