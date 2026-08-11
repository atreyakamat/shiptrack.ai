from backend.extensions import db

class PostalOffice(db.Model):
    __tablename__ = 'postal_office'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    code = db.Column(db.String(50))
    city = db.Column(db.String(100))
    state = db.Column(db.String(100))
    country = db.Column(db.String(100), default='India')
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)

    __table_args__ = (
        db.Index('idx_postal_office_name', 'name'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'code': self.code,
            'city': self.city,
            'state': self.state,
            'country': self.country,
            'latitude': self.latitude,
            'longitude': self.longitude
        }
