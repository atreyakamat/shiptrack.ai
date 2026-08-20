"""
Unit Tests for IndiaPostWebAdapter and Human-Assisted Table Extraction.
"""
import pytest
from unittest.mock import patch, MagicMock
from backend.carriers.india_post_web import IndiaPostWebAdapter
from backend.carriers.base import BaseCarrierAdapter
from backend.services.tracking_service import TrackingService

SAMPLE_INDIAPOST_HTML_RESULTS = """
<html>
<body>
    <table class="table table-bordered">
        <thead>
            <tr>
                <th>Booked At</th>
                <th>Booked On</th>
                <th>Destination Pincode</th>
                <th>Article Type</th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <td>Panaji NSH (403001)</td>
                <td>05/08/2026</td>
                <td>403107</td>
                <td>Speed Post</td>
            </tr>
        </tbody>
    </table>

    <table class="table table-striped">
        <thead>
            <tr>
                <th>Date</th>
                <th>Time</th>
                <th>Office</th>
                <th>Event</th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <td>05/08/2026</td>
                <td>12:15:00</td>
                <td>Panaji NSH</td>
                <td>Item Booked</td>
            </tr>
            <tr>
                <td>06/08/2026</td>
                <td>08:30:00</td>
                <td>Bicholim S.O</td>
                <td>Bag Received</td>
            </tr>
            <tr>
                <td>07/08/2026</td>
                <td>10:00:00</td>
                <td>Bambavada S.O</td>
                <td>Item Out for Delivery</td>
            </tr>
            <tr>
                <td>07/08/2026</td>
                <td>14:30:00</td>
                <td>Bambavada S.O</td>
                <td>Item Delivery Confirmed</td>
            </tr>
        </tbody>
    </table>
</body>
</html>
"""

SAMPLE_INDIAPOST_HTML_3COL = """
<html>
<body>
    <table>
        <tr><th>Date</th><th>Office</th><th>Event</th></tr>
        <tr><td>05/08/2026</td><td>Panaji NSH</td><td>Item Booked</td></tr>
        <tr><td>07/08/2026</td><td>Bambavada S.O</td><td>Item Delivered</td></tr>
    </table>
</body>
</html>
"""

SAMPLE_EMPTY_HTML = """
<html>
<body>
    <p>No consignment records found.</p>
</body>
</html>
"""

def test_web_adapter_tracking_number_validation():
    adapter = IndiaPostWebAdapter(headless=True)
    assert adapter.validate_tracking_number("EM740043207IN") is True
    assert adapter.validate_tracking_number("AB123456789IN") is True
    assert adapter.validate_tracking_number("INVALID123") is False
    assert adapter.validate_tracking_number("") is False

def test_web_adapter_extract_table_data():
    adapter = IndiaPostWebAdapter(headless=True)
    result = adapter.extract_table_data(SAMPLE_INDIAPOST_HTML_RESULTS, "EM740043207IN")
    
    details = result["details"]
    events = result["events"]
    
    assert details["tracking_number"] == "EM740043207IN"
    assert details["origin"] == "Panaji NSH (403001)"
    assert details["status"] == BaseCarrierAdapter.STATUS_DELIVERED
    assert len(events) == 4
    
    assert events[0]["date"] == "05/08/2026"
    assert events[0]["time"] == "12:15:00"
    assert events[0]["location"] == "Panaji NSH"
    assert events[0]["normalized_status"] == BaseCarrierAdapter.STATUS_BOOKED

    assert events[1]["normalized_status"] == BaseCarrierAdapter.STATUS_ARRIVED_AT_FACILITY
    assert events[2]["normalized_status"] == BaseCarrierAdapter.STATUS_OUT_FOR_DELIVERY
    assert events[3]["normalized_status"] == BaseCarrierAdapter.STATUS_DELIVERED

def test_web_adapter_extract_3col_table():
    adapter = IndiaPostWebAdapter(headless=True)
    result = adapter.extract_table_data(SAMPLE_INDIAPOST_HTML_3COL, "EM740043207IN")
    
    events = result["events"]
    assert len(events) == 2
    assert events[0]["location"] == "Panaji NSH"
    assert events[0]["time"] is None
    assert events[1]["normalized_status"] == BaseCarrierAdapter.STATUS_DELIVERED

def test_web_adapter_empty_table_returns_empty_events():
    adapter = IndiaPostWebAdapter(headless=True)
    result = adapter.extract_table_data(SAMPLE_EMPTY_HTML, "EM740043207IN")
    assert len(result["events"]) == 0
    assert result["details"]["status"] == BaseCarrierAdapter.STATUS_UNKNOWN

def test_tracking_service_provider_selection_web(app):
    with app.app_context():
        app.config['TRACKING_DEMO_MODE'] = False
        app.config['TRACKING_PROVIDER'] = 'web'
        adapter = TrackingService.get_carrier_adapter('india_post')
        assert isinstance(adapter, IndiaPostWebAdapter)

        app.config['TRACKING_DEMO_MODE'] = True
        app.config['TRACKING_PROVIDER'] = 'mock'
