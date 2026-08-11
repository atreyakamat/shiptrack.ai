from datetime import datetime, timezone
from backend.extensions import db

class OCRDocument(db.Model):
    __tablename__ = 'ocr_document'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    shipment_id = db.Column(db.Integer, db.ForeignKey('shipment.id'), nullable=True)
    filename = db.Column(db.String(255))
    file_path = db.Column(db.String(500))
    ocr_text = db.Column(db.Text)
    extracted_tracking_number = db.Column(db.String(50))
    confidence = db.Column(db.Float)
    processing_status = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            'id': self.id,
            'shipment_id': self.shipment_id,
            'filename': self.filename,
            'file_path': self.file_path,
            'ocr_text': self.ocr_text,
            'extracted_tracking_number': self.extracted_tracking_number,
            'confidence': self.confidence,
            'processing_status': self.processing_status,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
