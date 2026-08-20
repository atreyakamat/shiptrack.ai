import os
import logging
import time
from flask import Blueprint, request, jsonify, g
from werkzeug.utils import secure_filename
from backend.services.ocr_service import OCRService
from backend.utils.validators import ALLOWED_FILE_EXTENSIONS, validate_file_upload, generate_safe_filename
from backend.config import Config
from backend.extensions import db, limiter
from backend.models.ocr_document import OCRDocument
from backend.services.shipment_service import ShipmentService
from backend.utils.auth import token_required

logger = logging.getLogger(__name__)
ocr_bp = Blueprint('ocr', __name__)

@ocr_bp.route('/ocr', methods=['POST'])
@token_required
@limiter.limit("5 per minute")
def process_ocr():
    if 'file' not in request.files:
        return jsonify({'success': False, 'error': {'code': 'BAD_REQUEST', 'message': 'No file part'}}), 400
        
    file = request.files['file']
    if file.filename == '':
        return jsonify({'success': False, 'error': {'code': 'BAD_REQUEST', 'message': 'No selected file'}}), 400
        
    if file and validate_file_upload(file.filename):
        try:
            filename = generate_safe_filename(file.filename)
            upload_dir = Config.UPLOAD_FOLDER
            os.makedirs(upload_dir, exist_ok=True)
            file_path = os.path.join(upload_dir, filename)
            
            file.save(file_path)
            
            result = OCRService.process_image(file_path)
            
            doc = OCRDocument(
                user_id=g.current_user.id,
                filename=file.filename,
                file_path=file_path,
                ocr_text=result.get('full_text'),
                extracted_tracking_number=result.get('extracted_tracking_number'),
                confidence=result.get('confidence'),
                processing_status='completed'
            )
            db.session.add(doc)
            db.session.commit()
            
            # Cleanup immediately after processing to prevent unbounded storage growth
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
            except Exception as e:
                logger.error(f"Failed to cleanup OCR file {file_path}: {e}")
            
            data = doc.to_dict()
            data['candidates'] = result.get('candidates', [])
            # Inject demo flag from service if present
            if result.get('is_demo'):
                data['is_demo'] = True
                
            return jsonify({'success': True, 'data': data}), 200
            
        except Exception as e:
            logger.error(f"Error processing OCR: {e}")
            return jsonify({'success': False, 'error': {'code': 'OCR_ERROR', 'message': 'Failed to process OCR'}}), 500
            
    return jsonify({'success': False, 'error': {'code': 'BAD_REQUEST', 'message': 'Invalid file type'}}), 400

@ocr_bp.route('/ocr/confirm', methods=['POST'])
@token_required
@limiter.limit("20 per minute")
def confirm_ocr():
    try:
        data = request.json
        doc_id = data.get('document_id')
        tracking_number = data.get('tracking_number')
        
        doc = OCRDocument.query.filter_by(id=doc_id, user_id=g.current_user.id).first()
        if not doc:
            return jsonify({'success': False, 'error': {'code': 'NOT_FOUND', 'message': 'Document not found'}}), 404
            
        shipment = ShipmentService.create_shipment(g.current_user.id, {
            'tracking_number': tracking_number,
            'carrier': data.get('carrier', 'india_post')
        })
        
        doc.shipment_id = shipment.id
        db.session.commit()
        
        return jsonify({'success': True, 'data': shipment.to_dict()}), 201
    except ValueError as ve:
        db.session.rollback()
        err_msg = str(ve)
        if "already exists" in err_msg.lower():
            return jsonify({'success': False, 'error': {'code': 'DUPLICATE_SHIPMENT', 'message': "This tracking number is already in your shipments."}}), 409
        return jsonify({'success': False, 'error': {'code': 'VALIDATION_ERROR', 'message': err_msg}}), 422
    except Exception as e:
        logger.error(f"Error confirming OCR: {e}")
        return jsonify({'success': False, 'error': {'code': 'OCR_ERROR', 'message': 'Failed to confirm OCR'}}), 500
