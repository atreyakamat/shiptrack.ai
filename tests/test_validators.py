import pytest
from backend.utils.validators import validate_tracking_number, normalize_tracking_number

def test_validate_tracking_number_valid():
    assert validate_tracking_number('EM123456789IN', 'india_post') == True
    assert validate_tracking_number('EE987654321IN', 'india_post') == True

def test_validate_tracking_number_invalid():
    assert validate_tracking_number('INVALID123', 'india_post') == False
    assert validate_tracking_number('EM12345678IN', 'india_post') == False # Too short
    assert validate_tracking_number('1234567890123', 'india_post') == False # No letters

def test_normalize_tracking_number():
    assert normalize_tracking_number(' em123 456 789in ') == 'EM123456789IN'
    assert normalize_tracking_number('ee-987-654-321-in') == 'EE987654321IN'

def test_edge_cases():
    assert validate_tracking_number('', 'india_post') == False
    assert validate_tracking_number(None, 'india_post') == False
    assert normalize_tracking_number('') == ''
    assert normalize_tracking_number(None) == ''
