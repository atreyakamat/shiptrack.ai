import logging
import os
import re
from typing import Tuple, Dict, Any, Optional

logger = logging.getLogger(__name__)

try:
    import easyocr
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False
    logger.warning("easyocr not installed, OCR will mock or fail")

class OCRService:
    @staticmethod
    def extract_tracking_number(text: str) -> Optional[str]:
        # Simple regex for India Post
        match = re.search(r'[A-Z]{2}\d{9}IN', text.upper().replace(' ', ''))
        if match:
            return match.group(0)
        return None

    @staticmethod
    def process_image(file_path: str) -> Dict[str, Any]:
        result = {
            'extracted_tracking_number': None,
            'confidence': 0.0,
            'full_text': '',
            'other_detected_info': {}
        }
        
        if not OCR_AVAILABLE:
            logger.warning("OCR is not available (easyocr not installed). Using mock extraction for testing.")
            result['is_demo'] = True
            result['full_text'] = 'INDIA POST RECEIPT\nTRACKING NUMBER: EM740043207IN\nAMOUNT: 50.00'
            result['extracted_tracking_number'] = 'EM740043207IN'
            result['confidence'] = None # Explicitly set to None for demo
            return result
            
        try:
            reader = easyocr.Reader(['en'])
            ocr_result = reader.readtext(file_path)
            
            full_text = ' '.join([res[1] for res in ocr_result])
            result['full_text'] = full_text
            
            tracking_number = OCRService.extract_tracking_number(full_text)
            if tracking_number:
                result['extracted_tracking_number'] = tracking_number
                result['confidence'] = 0.85 # Mock confidence
                
            return result
        except Exception as e:
            logger.error(f"Error processing image {file_path}: {e}")
            return result
