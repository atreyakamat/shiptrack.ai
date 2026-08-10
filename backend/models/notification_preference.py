from backend.extensions import db

class NotificationPreference(db.Model):
    __tablename__ = 'notification_preference'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    event_type = db.Column(db.String(50), nullable=False)
    in_app = db.Column(db.Boolean, default=True)
    whatsapp = db.Column(db.Boolean, default=False)
    email = db.Column(db.Boolean, default=False)

    __table_args__ = (
        db.UniqueConstraint('user_id', 'event_type', name='uq_user_event'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'event_type': self.event_type,
            'in_app': self.in_app,
            'whatsapp': self.whatsapp,
            'email': self.email
        }
