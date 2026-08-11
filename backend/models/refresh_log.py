from datetime import datetime, timezone
from backend.extensions import db

class RefreshLog(db.Model):
    __tablename__ = 'refresh_log'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    shipment_id = db.Column(db.Integer, db.ForeignKey('shipment.id'), nullable=True)
    started_at = db.Column(db.DateTime)
    completed_at = db.Column(db.DateTime)
    status = db.Column(db.String(20))
    events_found = db.Column(db.Integer, default=0)
    error_message = db.Column(db.Text, nullable=True)

    def to_dict(self):
        return {
            'id': self.id,
            'shipment_id': self.shipment_id,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'status': self.status,
            'events_found': self.events_found,
            'error_message': self.error_message
        }
