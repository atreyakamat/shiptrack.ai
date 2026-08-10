from typing import List, Dict, Any
from .base import BaseCarrierAdapter
import re

class MockCarrierAdapter(BaseCarrierAdapter):
    def __init__(self):
        # 7 distinct scenarios as requested
        self.demo_data = {
            'EM100000001IN': {
                'details': {
                    'tracking_number': 'EM100000001IN',
                    'article_type': 'Speed Post (Mock Data)',
                    'origin': 'Delhi HO',
                    'destination': 'Bangalore',
                    'status': self.STATUS_BOOKED
                },
                'events': [
                    {'date': '09/08/2026', 'time': '10:00 AM', 'status': 'Item Booked', 'location': 'Delhi HO', 'raw_status': 'Item Booked'}
                ]
            },
            'EM100000002IN': {
                'details': {
                    'tracking_number': 'EM100000002IN',
                    'article_type': 'Registered Parcel (Mock Data)',
                    'origin': 'Mumbai GPO',
                    'destination': 'Pune',
                    'status': self.STATUS_IN_TRANSIT
                },
                'events': [
                    {'date': '08/08/2026', 'time': '10:00 AM', 'status': 'Item Booked', 'location': 'Mumbai GPO', 'raw_status': 'Item Booked'},
                    {'date': '08/08/2026', 'time': '06:00 PM', 'status': 'Bag Received', 'location': 'Mumbai NSH', 'raw_status': 'Bag Received'},
                    {'date': '09/08/2026', 'time': '02:00 AM', 'status': 'Item Dispatched', 'location': 'Pune Sorting Hub', 'raw_status': 'Item Dispatched'}
                ]
            },
            'EM100000003IN': {
                'details': {
                    'tracking_number': 'EM100000003IN',
                    'article_type': 'Speed Post (Mock Data)',
                    'origin': 'Bicholim Industrial Estate S.O, Goa',
                    'destination': 'Bambavada S.O',
                    'status': self.STATUS_OUT_FOR_DELIVERY
                },
                'events': [
                    {'date': '05/08/2026', 'time': '12:15 PM', 'status': 'Item Booked', 'location': 'Bicholim Industrial Estate S.O, Goa', 'raw_status': 'Item Booked'},
                    {'date': '07/08/2026', 'time': '09:30 AM', 'status': 'Item Received', 'location': 'Bambavada S.O', 'raw_status': 'Item Received'},
                    {'date': '07/08/2026', 'time': '02:15 PM', 'status': 'Item Out for Delivery', 'location': 'Bambavada S.O', 'raw_status': 'Item Out for Delivery'}
                ]
            },
            'EM100000004IN': {
                'details': {
                    'tracking_number': 'EM100000004IN',
                    'article_type': 'Speed Post (Mock Data)',
                    'origin': 'Mapusa HO, Goa',
                    'destination': 'Mumbai',
                    'status': self.STATUS_DELIVERED
                },
                'events': [
                    {'date': '01/08/2026', 'time': '10:00 AM', 'status': 'Item Booked', 'location': 'Mapusa HO, Goa', 'raw_status': 'Item Booked'},
                    {'date': '03/08/2026', 'time': '08:00 AM', 'status': 'Item Out for Delivery', 'location': 'Mumbai', 'raw_status': 'Item Out for Delivery'},
                    {'date': '03/08/2026', 'time': '11:30 AM', 'status': 'Item Delivered', 'location': 'Mumbai', 'raw_status': 'Item Delivered at Mumbai'}
                ]
            },
            'EM100000005IN': {
                'details': {
                    'tracking_number': 'EM100000005IN',
                    'article_type': 'Speed Post (Mock Data)',
                    'origin': 'Kolkata',
                    'destination': 'Pune',
                    'status': self.STATUS_EXCEPTION
                },
                'events': [
                    {'date': '01/08/2026', 'time': '10:00 AM', 'status': 'Item Booked', 'location': 'Kolkata', 'raw_status': 'Item Booked'},
                    {'date': '02/08/2026', 'time': '02:00 PM', 'status': 'Exception', 'location': 'Nagpur Transit', 'raw_status': 'Item Delayed / Misrouted'}
                ]
            }
        }
        
        # Scenarios mapping to testing inputs:
        # EM100000001IN -> Booked
        # EM100000002IN -> In Transit
        # EM100000003IN -> Out for Delivery
        # EM100000004IN -> Delivered
        # EM100000005IN -> Delayed/Exception
        # EM100000006IN -> No Tracking Data (Empty events, valid details)
        self.demo_data['EM100000006IN'] = {
            'details': {
                'tracking_number': 'EM100000006IN',
                'article_type': 'Unknown (Mock Data)',
                'origin': None,
                'destination': None,
                'status': self.STATUS_UNKNOWN
            },
            'events': []
        }
        
        # EM100000007IN -> Tracking Error (Raises exception)
        # Will handle in track method
        
        # Keep old mock data for backward compatibility in tests
        self.demo_data['EM740043207IN'] = self.demo_data['EM100000003IN']
        self.demo_data['EE123456789IN'] = self.demo_data['EM100000004IN']
        self.demo_data['EM123987456IN'] = self.demo_data['EM100000001IN']

    def track(self, tracking_number: str) -> Dict[str, Any]:
        if tracking_number == 'EM100000007IN':
            raise Exception('Mock Tracking Error: Connection Timeout')
            
        return self.demo_data.get(tracking_number, {})

    def get_tracking_history(self, tracking_number: str) -> List[Dict[str, Any]]:
        if tracking_number == 'EM100000007IN':
            raise Exception('Mock Tracking Error: Connection Timeout')
            
        data = self.demo_data.get(tracking_number, {})
        return data.get('events', [])

    def validate_tracking_number(self, tracking_number: str) -> bool:
        return bool(re.match(r'^[A-Z]{2}[0-9]{9}IN$', tracking_number))

    def normalize_status(self, raw_status: str) -> str:
        s = raw_status.lower()
        if 'delivered' in s: return self.STATUS_DELIVERED
        if 'out for delivery' in s: return self.STATUS_OUT_FOR_DELIVERY
        if 'booked' in s: return self.STATUS_BOOKED
        if 'dispatched' in s: return self.STATUS_DISPATCHED
        if 'received' in s or 'bagged' in s: return self.STATUS_IN_TRANSIT
        if 'exception' in s or 'delay' in s: return self.STATUS_EXCEPTION
        return self.STATUS_UNKNOWN
