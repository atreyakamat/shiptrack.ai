import re
import os

ALLOWED_FILE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'pdf'}

def validate_tracking_number(number: str, carrier: str = 'india_post') -> bool:
    if not number:
        return False
    number = normalize_tracking_number(number)
    if carrier == 'india_post':
        return bool(re.match(r'^[A-Z]{2}\d{9}IN$', number))
    return True

def normalize_tracking_number(number: str) -> str:
    if not number:
        return ''
    # Remove all whitespace (spaces, tabs, newlines) and hyphens, convert to uppercase
    return re.sub(r'[\s\-]+', '', number.upper())

CARRIER_LABEL_TO_CODE = {
    'India Post': 'india_post',
    'Delhivery': 'delhivery',
    'BlueDart': 'bluedart',
    'DTDC': 'dtdc',
    'india_post': 'india_post',
    'mock': 'mock',
}

def validate_carrier(carrier: str) -> bool:
    supported_carriers = ['india_post', 'mock', 'delhivery', 'bluedart', 'dtdc']
    code = CARRIER_LABEL_TO_CODE.get(carrier, carrier)
    return code in supported_carriers

def normalize_carrier(carrier: str) -> str:
    return CARRIER_LABEL_TO_CODE.get(carrier, carrier)

def validate_file_upload(filename: str, max_size: int = 16 * 1024 * 1024) -> bool:
    if not filename:
        return False
    ext = filename.rsplit('.', 1)[-1].lower()
    return '.' in filename and ext in ALLOWED_FILE_EXTENSIONS

def generate_safe_filename(filename: str) -> str:
    import uuid
    from werkzeug.utils import secure_filename
    
    sec_name = secure_filename(filename)
    name, ext = os.path.splitext(sec_name)
    return f"{name}_{uuid.uuid4().hex}{ext}"
