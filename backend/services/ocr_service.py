import logging
import os
import re
from typing import Tuple, Dict, Any, Optional, List

logger = logging.getLogger(__name__)

try:
    import cv2
    import numpy as np
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False
    logger.warning("opencv-python-headless not installed, OCR preprocessing disabled")

try:
    import easyocr
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False
    logger.warning("easyocr not installed, OCR will mock or fail")

class OCRService:
    @staticmethod
    def preprocess_image(file_path: str) -> str:
        if not CV2_AVAILABLE:
            return file_path
        
        try:
            img = cv2.imread(file_path)
            # Convert to grayscale
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            # Increase contrast
            alpha = 1.5
            beta = 0
            adjusted = cv2.convertScaleAbs(gray, alpha=alpha, beta=beta)
            
            # Simple thresholding
            _, thresh = cv2.threshold(adjusted, 150, 255, cv2.THRESH_TRUNC)
            
            proc_path = file_path + "_proc.jpg"
            cv2.imwrite(proc_path, thresh)
            return proc_path
        except Exception as e:
            logger.error(f"Error during OCR preprocessing: {e}")
            return file_path

    @staticmethod
    def extract_tracking_number(text: str) -> Optional[Tuple[str, float]]:
        # Regex for India Post e.g. EM123456789IN
        # Account for common OCR errors: O/0, I/1, S/5
        clean_text = text.upper().replace(' ', '').replace('-', '')
        
        # Standard strict match
        match = re.search(r'([A-Z]{2})(\d{9})(IN)', clean_text)
        if match:
            return match.group(0), 0.95
            
        # Looser match allowing some numeric confusion
        # This will need a confidence penalty
        loose_match = re.search(r'([A-Z0-9]{2})([0-9OIS]{9})(IN)', clean_text)
        if loose_match:
            candidate = loose_match.group(0)
            # Correct common confusions in the numeric part
            prefix = candidate[:2]
            nums = candidate[2:11]
            suffix = candidate[11:]
            nums = nums.replace('O', '0').replace('I', '1').replace('S', '5')
            corrected = prefix + nums + suffix
            return corrected, 0.60
            
        return None, 0.0

    @staticmethod
    def extract_candidates(text: str) -> List[Dict[str, Any]]:
        # Clean text
        clean_text = text.upper().replace(' ', '').replace('-', '')
        
        candidates = []
        seen = set()
        
        # 1. Strict matches
        strict_matches = re.finditer(r'([A-Z]{2})(\d{9})(IN)', clean_text)
        for m in strict_matches:
            val = m.group(0)
            if val not in seen:
                seen.add(val)
                candidates.append({'tracking_number': val, 'confidence': 0.95})
                
        # 2. Loose matches (allowing O/I/S confusion)
        loose_matches = re.finditer(r'([A-Z0-9]{2})([0-9OIS]{9})(IN)', clean_text)
        for m in loose_matches:
            val = m.group(0)
            # Correct common confusions in the numeric part
            prefix = val[:2]
            nums = val[2:11]
            suffix = val[11:]
            nums = nums.replace('O', '0').replace('I', '1').replace('S', '5')
            corrected = prefix + nums + suffix
            
            if corrected not in seen:
                seen.add(corrected)
                candidates.append({'tracking_number': corrected, 'confidence': 0.60})
                
        return sorted(candidates, key=lambda x: x['confidence'], reverse=True)

    @staticmethod
    def process_image(file_path: str) -> Dict[str, Any]:
        result = {
            'extracted_tracking_number': None,
            'confidence': 0.0,
            'full_text': '',
            'other_detected_info': {},
            'candidates': []
        }
        
        if not OCR_AVAILABLE:
            logger.warning("OCR is not available (easyocr not installed). Using mock extraction for testing.")
            result['is_demo'] = True
            result['full_text'] = 'INDIA POST RECEIPT\nTRACKING NUMBER: EM740043207IN\nSECOND NUMBER: EE123456789IN\nAMOUNT: 50.00'
            result['extracted_tracking_number'] = 'EM740043207IN'
            result['confidence'] = None # Explicitly set to None for demo
            result['candidates'] = [
                {'tracking_number': 'EM740043207IN', 'confidence': 0.95},
                {'tracking_number': 'EE123456789IN', 'confidence': 0.60}
            ]
            return result
            
        try:
            proc_path = OCRService.preprocess_image(file_path)
            
            reader = easyocr.Reader(['en'])
            ocr_result = reader.readtext(proc_path)
            
            full_text = ' '.join([res[1] for res in ocr_result])
            result['full_text'] = full_text
            
            candidates = OCRService.extract_candidates(full_text)
            result['candidates'] = candidates
            
            if candidates:
                result['extracted_tracking_number'] = candidates[0]['tracking_number']
                result['confidence'] = candidates[0]['confidence']
                
            if proc_path != file_path and os.path.exists(proc_path):
                os.remove(proc_path)
                
            return result
        except Exception as e:
            logger.error(f"Error processing image {file_path}: {e}")
            return result
