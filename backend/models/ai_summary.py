from datetime import datetime, timezone
from backend.extensions import db

class AISummary(db.Model):
    __tablename__ = 'ai_summary'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    shipment_id = db.Column(db.Integer, db.ForeignKey('shipment.id'), nullable=False)
    summary = db.Column(db.Text)
    delay_analysis = db.Column(db.Text)
    prediction = db.Column(db.Text)
    health_status = db.Column(db.String(20))
    model = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            'id': self.id,
            'shipment_id': self.shipment_id,
            'summary': self.summary,
            'delay_analysis': self.delay_analysis,
            'prediction': self.prediction,
            'health_status': self.health_status,
            'model': self.model,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
