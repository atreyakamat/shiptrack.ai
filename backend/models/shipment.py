from datetime import datetime, timezone
from backend.extensions import db

class Shipment(db.Model):
    __tablename__ = 'shipment'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    tracking_number = db.Column(db.String(20), nullable=False)
    carrier = db.Column(db.String(50), default='india_post')
    description = db.Column(db.String(500))
    category = db.Column(db.String(50), default='general')
    status = db.Column(db.String(20), default='BOOKED')
    current_location = db.Column(db.String(200))
    origin = db.Column(db.String(200))
    destination = db.Column(db.String(200))
    booked_at = db.Column(db.DateTime)
    last_updated = db.Column(db.DateTime)
    expected_delivery = db.Column(db.DateTime, nullable=True)
    priority = db.Column(db.String(10), default='normal')
    notes = db.Column(db.Text)
    is_archived = db.Column(db.Boolean, default=False)
    article_type = db.Column(db.String(100))
    tariff = db.Column(db.String(50))
    origin_pincode = db.Column(db.String(10))
    destination_pincode = db.Column(db.String(10))
    last_successful_sync = db.Column(db.DateTime)
    last_attempted_sync = db.Column(db.DateTime)
    last_failed_sync = db.Column(db.DateTime)
    last_error = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        db.UniqueConstraint('carrier', 'tracking_number', name='uq_carrier_tracking'),
        db.Index('idx_shipment_status', 'status'),
        db.Index('idx_shipment_created_at', 'created_at'),
        db.Index('idx_shipment_updated_at', 'updated_at'),
    )

    tracking_events = db.relationship('TrackingEvent', backref='shipment', lazy=True, cascade='all, delete-orphan')
    ocr_documents = db.relationship('OCRDocument', backref='shipment', lazy=True)
    ai_summaries = db.relationship('AISummary', backref='shipment', lazy=True, cascade='all, delete-orphan')
    notifications = db.relationship('Notification', backref='shipment', lazy=True, cascade='all, delete-orphan')
    refresh_logs = db.relationship('RefreshLog', backref='shipment', lazy=True, cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'tracking_number': self.tracking_number,
            'carrier': self.carrier,
            'description': self.description,
            'category': self.category,
            'status': self.status,
            'current_location': self.current_location,
            'origin': self.origin,
            'destination': self.destination,
            'booked_at': self.booked_at.isoformat() if self.booked_at else None,
            'last_updated': self.last_updated.isoformat() if self.last_updated else None,
            'expected_delivery': self.expected_delivery.isoformat() if self.expected_delivery else None,
            'priority': self.priority,
            'notes': self.notes,
            'is_archived': self.is_archived,
            'article_type': self.article_type,
            'tariff': self.tariff,
            'origin_pincode': self.origin_pincode,
            'destination_pincode': self.destination_pincode,
            'last_successful_sync': self.last_successful_sync.isoformat() if self.last_successful_sync else None,
            'last_attempted_sync': self.last_attempted_sync.isoformat() if self.last_attempted_sync else None,
            'last_failed_sync': self.last_failed_sync.isoformat() if self.last_failed_sync else None,
            'last_error': self.last_error,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
