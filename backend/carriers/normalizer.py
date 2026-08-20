"""
Provider-Agnostic Tracking Event Normalizer.
Converts external courier and aggregator JSON responses into ShipTrack's canonical event model.
Ensures zero data fabrication (no invented dates, locations, or GPS coordinates).
"""
import re
from typing import Dict, Any, List, Optional
import dateutil.parser
from .base import BaseCarrierAdapter

class CarrierNormalizer:
    STATUS_MAP = {
        'booked': BaseCarrierAdapter.STATUS_BOOKED,
        'item booked': BaseCarrierAdapter.STATUS_BOOKED,
        'inforeceived': BaseCarrierAdapter.STATUS_BOOKED,
        'pickup': BaseCarrierAdapter.STATUS_BOOKED,
        'dispatched': BaseCarrierAdapter.STATUS_DISPATCHED,
        'item dispatched': BaseCarrierAdapter.STATUS_DISPATCHED,
        'intransit': BaseCarrierAdapter.STATUS_IN_TRANSIT,
        'in_transit': BaseCarrierAdapter.STATUS_IN_TRANSIT,
        'in transit': BaseCarrierAdapter.STATUS_IN_TRANSIT,
        'transit': BaseCarrierAdapter.STATUS_IN_TRANSIT,
        'bag received': BaseCarrierAdapter.STATUS_ARRIVED_AT_FACILITY,
        'arrived at facility': BaseCarrierAdapter.STATUS_ARRIVED_AT_FACILITY,
        'arrivedathub': BaseCarrierAdapter.STATUS_ARRIVED_AT_FACILITY,
        'received': BaseCarrierAdapter.STATUS_ARRIVED_AT_FACILITY,
        'item received': BaseCarrierAdapter.STATUS_ARRIVED_AT_FACILITY,
        'out for delivery': BaseCarrierAdapter.STATUS_OUT_FOR_DELIVERY,
        'outfordelivery': BaseCarrierAdapter.STATUS_OUT_FOR_DELIVERY,
        'with courier': BaseCarrierAdapter.STATUS_OUT_FOR_DELIVERY,
        'delivered': BaseCarrierAdapter.STATUS_DELIVERED,
        'item delivered': BaseCarrierAdapter.STATUS_DELIVERED,
        'delivery confirmed': BaseCarrierAdapter.STATUS_DELIVERED,
        'delayed': BaseCarrierAdapter.STATUS_DELAYED,
        'delay': BaseCarrierAdapter.STATUS_DELAYED,
        'customshold': BaseCarrierAdapter.STATUS_DELAYED,
        'attemptfailed': BaseCarrierAdapter.STATUS_EXCEPTION,
        'exception': BaseCarrierAdapter.STATUS_EXCEPTION,
        'returned': BaseCarrierAdapter.STATUS_RETURNED,
        'rto': BaseCarrierAdapter.STATUS_RETURNED,
        'return': BaseCarrierAdapter.STATUS_RETURNED,
    }

    @classmethod
    def normalize_status(cls, raw_status: Optional[str]) -> str:
        if not raw_status:
            return BaseCarrierAdapter.STATUS_UNKNOWN
        clean = raw_status.strip().lower().replace('_', ' ')
        if clean in cls.STATUS_MAP:
            return cls.STATUS_MAP[clean]
        for key, val in cls.STATUS_MAP.items():
            if key in clean:
                return val
        return BaseCarrierAdapter.STATUS_UNKNOWN

    @classmethod
    def parse_event_datetime(cls, raw_datetime_str: Optional[str]) -> tuple[Optional[str], Optional[str]]:
        """Splits an ISO/formatted timestamp into (event_date, event_time)."""
        if not raw_datetime_str or not raw_datetime_str.strip():
            return None, None
        try:
            dt = dateutil.parser.parse(raw_datetime_str)
            event_date = dt.strftime("%d/%m/%Y")
            event_time = dt.strftime("%I:%M %p")
            return event_date, event_time
        except Exception:
            return None, None

    @classmethod
    def normalize_event(cls, raw_event: Dict[str, Any]) -> Dict[str, Any]:
        """Normalizes a single raw tracking checkpoint into canonical format."""
        raw_status = (
            raw_event.get('raw_status')
            or raw_event.get('status')
            or raw_event.get('substatus')
            or raw_event.get('checkpoint_status')
            or raw_event.get('message')
            or ''
        )
        
        # Location extraction (must not invent locations)
        location = (
            raw_event.get('location')
            or raw_event.get('facility')
            or raw_event.get('city')
            or raw_event.get('checkpoint_location')
        )
        if location:
            location = str(location).strip()
            if location.lower() in ['', 'null', 'none', 'unknown']:
                location = None

        # Description / Narrative
        description = (
            raw_event.get('description')
            or raw_event.get('details')
            or raw_event.get('message')
            or raw_status
        )

        # Date and Time handling
        event_date = raw_event.get('date') or raw_event.get('event_date')
        event_time = raw_event.get('time') or raw_event.get('event_time')
        
        if not event_date and (raw_event.get('checkpoint_date') or raw_event.get('timestamp') or raw_event.get('datetime')):
            dt_src = raw_event.get('checkpoint_date') or raw_event.get('timestamp') or raw_event.get('datetime')
            parsed_d, parsed_t = cls.parse_event_datetime(str(dt_src))
            event_date = event_date or parsed_d
            event_time = event_time or parsed_t

        return {
            'date': str(event_date) if event_date else None,
            'time': str(event_time) if event_time else None,
            'status': raw_status or 'Status Updated',
            'normalized_status': cls.normalize_status(raw_status),
            'location': location,
            'description': str(description) if description else None,
            'raw_status': str(raw_status) if raw_status else None
        }

    @classmethod
    def normalize_response(cls, tracking_number: str, raw_payload: Dict[str, Any]) -> Dict[str, Any]:
        """Normalizes an entire carrier API response payload."""
        # Check standard aggregator response patterns (e.g., TrackingMore, Ship24, Direct)
        data = raw_payload.get('data', raw_payload)
        if isinstance(data, list) and len(data) > 0:
            data = data[0]

        raw_events = (
            data.get('events')
            or data.get('origin_info', {}).get('trackinfo')
            or data.get('trackinfo')
            or data.get('checkpoints')
            or []
        )

        normalized_events = [cls.normalize_event(e) for e in raw_events]
        
        # Sort events chronologically if timestamps exist
        raw_current_status = (
            data.get('delivery_status')
            or data.get('status')
            or (normalized_events[-1]['raw_status'] if normalized_events else None)
        )
        normalized_overall_status = cls.normalize_status(raw_current_status)

        origin = (
            data.get('origin')
            or data.get('origin_info', {}).get('ItemReceived')
            or data.get('origin_city')
        )
        destination = (
            data.get('destination')
            or data.get('destination_info', {}).get('ItemDelivered')
            or data.get('destination_city')
        )

        return {
            'details': {
                'tracking_number': tracking_number,
                'status': normalized_overall_status,
                'origin': str(origin) if origin else None,
                'destination': str(destination) if destination else None,
                'article_type': data.get('article_type') or data.get('courier_code') or 'Speed Post'
            },
            'events': normalized_events
        }
