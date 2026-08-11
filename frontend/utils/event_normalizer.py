import streamlit as st
from datetime import datetime
from typing import Dict, Any, Optional, List


def normalize_tracking_event(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalize a tracking event from any source (SQLAlchemy model, API response, dict)
    into a canonical format for frontend rendering.
    
    Returns:
        {
            "status": str,
            "title": str,
            "description": str,
            "location": str,
            "event_timestamp": str (ISO 8601 format),
            "date_display": str (formatted as "11 Aug 2026"),
            "time_display": str (formatted as "09:07 AM"),
            "icon": str (emoji)
        }
    """
    if not event:
        return _empty_event()
    
    # Extract raw fields with fallbacks
    raw_status = event.get('status') or event.get('raw_status') or 'Tracking Update'
    raw_location = event.get('location')
    raw_description = event.get('description')
    raw_timestamp = event.get('event_timestamp') or event.get('timestamp') or event.get('created_at')
    
    # Normalize status
    status = str(raw_status).strip() if raw_status else 'Tracking Update'
    
    # Normalize location
    location = _clean_value(raw_location, 'Location unavailable')
    
    # Normalize description
    description = _clean_value(raw_description)
    
    # Normalize timestamp to ISO format
    iso_timestamp = _normalize_timestamp(raw_timestamp)
    
    # Format for display
    date_display, time_display = _format_timestamp_for_display(iso_timestamp)
    
    # Get status icon
    icon = get_status_icon(status)
    
    return {
        'status': status,
        'title': status,
        'description': description,
        'location': location,
        'event_timestamp': iso_timestamp,
        'date_display': date_display,
        'time_display': time_display,
        'icon': icon,
        'is_latest': False  # Set by caller
    }


def _empty_event() -> Dict[str, Any]:
    return {
        'status': 'Tracking Update',
        'title': 'Tracking Update',
        'description': '',
        'location': 'Location unavailable',
        'event_timestamp': '',
        'date_display': 'Date unavailable',
        'time_display': 'Time unavailable',
        'icon': '📍',
        'is_latest': False
    }


def _clean_value(value: Any, fallback: str = '') -> str:
    """Clean a value, returning fallback for None, 'None', 'null', empty strings."""
    if value is None:
        return fallback
    s = str(value).strip()
    if not s or s.lower() in ('none', 'null', 'undefined', 'nan'):
        return fallback
    return s


def _normalize_timestamp(ts: Any) -> str:
    """
    Convert various timestamp formats to ISO 8601 (YYYY-MM-DDTHH:MM:SS).
    Handles:
    - ISO format: 2026-08-11T09:07:44
    - ISO with Z: 2026-08-11T09:07:44Z
    - Date only: 2026-08-11
    - DD/MM/YYYY: 11/08/2026
    - DD/MM/YYYYTHH:MM AM/PM: 11/08/2026T09:07 AM
    - datetime objects
    """
    if not ts:
        return ''
    
    # Already a datetime object
    if isinstance(ts, datetime):
        return ts.isoformat()
    
    ts_str = str(ts).strip()
    if not ts_str:
        return ''
    
    # If already ISO format with T separator
    if 'T' in ts_str and ts_str.count('-') >= 2:
        # Check if it's YYYY-MM-DDTHH:MM:SS format
        parts = ts_str.split('T')
        if len(parts) == 2 and len(parts[0]) == 10 and parts[0].count('-') == 2:
            # Already good ISO format, maybe truncate to seconds
            time_part = parts[1][:8]  # HH:MM:SS
            return f"{parts[0]}T{time_part}"
    
    # Try parsing DD/MM/YYYYTHH:MM AM/PM format (from mock data)
    if 'T' in ts_str and '/' in ts_str:
        try:
            dt = datetime.strptime(ts_str[:22], "%d/%m/%YT%I:%M %p")
            return dt.isoformat()
        except ValueError:
            pass
    
    # Try parsing DD/MM/YYYY HH:MM AM/PM
    if '/' in ts_str and ':' in ts_str:
        try:
            dt = datetime.strptime(ts_str[:21], "%d/%m/%Y %I:%M %p")
            return dt.isoformat()
        except ValueError:
            pass
    
    # Try parsing YYYY-MM-DD
    if len(ts_str) >= 10 and ts_str.count('-') == 2:
        try:
            dt = datetime.strptime(ts_str[:10], "%Y-%m-%d")
            return dt.isoformat()
        except ValueError:
            pass
    
    # Try parsing DD/MM/YYYY
    if len(ts_str) >= 10 and ts_str.count('/') == 2:
        try:
            dt = datetime.strptime(ts_str[:10], "%d/%m/%Y")
            return dt.isoformat()
        except ValueError:
            pass
    
    # Fallback: return as-is
    return ts_str


def _format_timestamp_for_display(iso_ts: str) -> tuple:
    """Format ISO timestamp for display as (date_str, time_str)."""
    if not iso_ts:
        return 'Date unavailable', 'Time unavailable'
    
    try:
        # Parse ISO format
        if 'T' in iso_ts:
            dt = datetime.fromisoformat(iso_ts.replace('Z', '+00:00'))
        else:
            dt = datetime.fromisoformat(iso_ts)
        
        date_str = dt.strftime("%d %b %Y")
        time_str = dt.strftime("%I:%M %p")
        return date_str, time_str
    except Exception:
        # If parsing fails, try to extract parts
        if 'T' in iso_ts:
            parts = iso_ts.split('T')
            date_part = parts[0]
            time_part = parts[1][:5] if len(parts) > 1 else ''
            
            # Try to format date part
            try:
                if '-' in date_part:
                    dt = datetime.strptime(date_part[:10], "%Y-%m-%d")
                    date_str = dt.strftime("%d %b %Y")
                elif '/' in date_part:
                    dt = datetime.strptime(date_part[:10], "%d/%m/%Y")
                    date_str = dt.strftime("%d %b %Y")
                else:
                    date_str = date_part
            except Exception:
                date_str = date_part
            
            return date_str, time_part if time_part else 'Time unavailable'
        
        return iso_ts, 'Time unavailable'


def get_status_icon(status: str) -> str:
    """Get emoji icon for a status."""
    s = str(status).lower()
    if 'delivered' in s:
        return "✅"
    if 'out for delivery' in s or 'out for delivery' in s:
        return "🛵"
    if 'transit' in s or 'dispatched' in s or 'arrived' in s or 'facility' in s or 'received' in s or 'bagged' in s:
        return "🚚"
    if 'booked' in s or 'bagged' in s:
        return "📦"
    if 'delayed' in s or 'exception' in s:
        return "⚠️"
    return "📍"


def normalize_tracking_events(events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Normalize a list of tracking events, marking the first as latest."""
    normalized = [normalize_tracking_event(e) for e in events]
    if normalized:
        normalized[0]['is_latest'] = True
    return normalized


# Canonical status order for progress bar
STATUS_STAGES = [
    ("Booked", "📦"),
    ("Dispatched", "📤"),
    ("In Transit", "🚚"),
    ("Out for Delivery", "🛵"),
    ("Delivered", "✅"),
]

STATUS_KEYWORDS = {
    0: ['booked'],
    1: ['dispatched'],
    2: ['transit', 'arrived', 'facility', 'received', 'bagged'],
    3: ['out for delivery', 'out_for_delivery'],
    4: ['delivered'],
    # Delayed/exception map to In Transit
    -1: ['delayed', 'exception', 'return'],
}


def get_progress_index(status: str) -> int:
    """Map a status string to the progress bar stage index (0-4)."""
    if not status:
        return 0
    
    s = str(status).lower().replace('_', ' ')
    
    # Check for delivered first (highest priority)
    if any(kw in s for kw in STATUS_KEYWORDS[4]):
        return 4
    
    # Check for out for delivery
    if any(kw in s for kw in STATUS_KEYWORDS[3]):
        return 3
    
    # Check for in transit
    if any(kw in s for kw in STATUS_KEYWORDS[2]):
        return 2
    
    # Check for dispatched
    if any(kw in s for kw in STATUS_KEYWORDS[1]):
        return 1
    
    # Check for booked
    if any(kw in s for kw in STATUS_KEYWORDS[0]):
        return 0
    
    # Check for delayed/exception -> map to In Transit
    if any(kw in s for kw in STATUS_KEYWORDS[-1]):
        return 2
    
    return 0


def get_progress_status_label(index: int) -> str:
    """Get the display label for a progress stage index."""
    if 0 <= index < len(STATUS_STAGES):
        return STATUS_STAGES[index][0]
    return STATUS_STAGES[0][0]


def get_progress_status_icon(index: int) -> str:
    """Get the icon for a progress stage index."""
    if 0 <= index < len(STATUS_STAGES):
        return STATUS_STAGES[index][1]
    return STATUS_STAGES[0][1]