import pytest
from backend.services.ocr_service import OCRService
from backend.utils.validators import normalize_tracking_number, validate_tracking_number

def test_normalize_tracking_number():
    assert normalize_tracking_number("em123456789in") == "EM123456789IN"
    assert normalize_tracking_number(" EM 123 456 789 IN ") == "EM123456789IN"
    assert normalize_tracking_number("EM-123-456-789-IN") == "EM123456789IN"
    assert normalize_tracking_number("EM\n123456789\tIN") == "EM123456789IN"
    assert normalize_tracking_number("") == ""

def test_validate_tracking_number():
    assert validate_tracking_number("EM123456789IN", "india_post") == True
    assert validate_tracking_number("AA123456789IN", "india_post") == True
    assert validate_tracking_number("EM123456789IN", "mock") == True
    assert validate_tracking_number("123456789IN", "india_post") == False
    assert validate_tracking_number("EMA123456789IN", "india_post") == False
    assert validate_tracking_number("EM123456789I", "india_post") == False
    assert validate_tracking_number("", "india_post") == False

def test_extract_tracking_number_valid():
    text = "RECEIPT\nTRACKING ID: EM123456789IN\nDATE: 01/01/2026"
    res = OCRService.extract_tracking_number(text)
    assert res is not None
    assert res[0] == "EM123456789IN"

def test_extract_tracking_number_with_noise():
    text = "IN EM123456789IN 1234 INDIA POST"
    res = OCRService.extract_tracking_number(text)
    assert res is not None
    assert res[0] == "EM123456789IN"

def test_extract_tracking_number_invalid():
    text = "RECEIPT\nTRACKING ID: 123456\nDATE: 01/01/2026"
    res = OCRService.extract_tracking_number(text)
    assert res[0] is None
