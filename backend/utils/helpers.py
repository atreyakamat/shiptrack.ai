from datetime import datetime
import dateutil.parser

STATUS_DISPLAY_NAMES = {
    'BOOKED': 'Booked',
    'DISPATCHED': 'Dispatched',
    'IN_TRANSIT': 'In Transit',
    'OUT_FOR_DELIVERY': 'Out for Delivery',
    'DELIVERED': 'Delivered',
    'EXCEPTION': 'Exception',
    'UNKNOWN': 'Unknown'
}

def parse_date(date_str: str) -> datetime:
    try:
        if not date_str:
            return None
        return dateutil.parser.parse(date_str)
    except Exception:
        return None

def format_datetime(dt: datetime) -> str:
    if not dt:
        return ""
    return dt.isoformat()

def get_greeting() -> str:
    hour = datetime.now().hour
    if hour < 12:
        return "Good morning"
    elif hour < 18:
        return "Good afternoon"
    else:
        return "Good evening"

def calculate_days_between(start: datetime, end: datetime) -> int:
    if not start or not end:
        return 0
    return (end - start).days
