from datetime import datetime, timezone
from backend.extensions import db

class Notification(db.Model):
    __tablename__ = 'notification'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    shipment_id = db.Column(db.Integer, db.ForeignKey('shipment.id'), nullable=True)
    channel = db.Column(db.String(20))
    notification_type = db.Column(db.String(50))
    message = db.Column(db.Text)
    status = db.Column(db.String(20), default='unread')
    sent_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            'id': self.id,
            'shipment_id': self.shipment_id,
            'channel': self.channel,
            'notification_type': self.notification_type,
            'message': self.message,
            'status': self.status,
            'sent_at': self.sent_at.isoformat() if self.sent_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
