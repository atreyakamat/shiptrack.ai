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


# Regression: India Post obfuscates real values onto <canvas> with the true text in
# aria-label, and injects hidden [data-fake] decoy spans. The adapter must read the
# aria-labels and drop decoys.
OBFUSCATED_HTML = """
<html><body>
<div><span>Article Type:</span>
  <span role="img" aria-label="SP_INLAND_DOC"><canvas aria-hidden="true"></canvas></span>
  <span aria-hidden="true" style="left:-9999px"><span data-fake="junk1">XXjunk1YY</span></span>
</div>
<div><span>Booked At:</span>
  <span role="img" aria-label="Goregaon RS SO"><canvas></canvas></span></div>
<div><span>Destination:</span>
  <span role="img" aria-label="Tivim S.O"><canvas></canvas></span></div>
<table>
  <tr><th>Event</th><th>Date</th><th>Time</th><th>Office</th><th>Remarks</th></tr>
  <tr>
    <td><span role="img" aria-label="Item Booked"><canvas></canvas></span><span data-fake="d">XXdecoyYY</span></td>
    <td><span role="img" aria-label="22/10/2026"></span></td>
    <td><span role="img" aria-label="17:35:49"></span></td>
    <td><span role="img" aria-label="Goregaon RS SO"></span></td>
    <td><span role="img" aria-label="-"></span></td>
  </tr>
  <tr>
    <td><span role="img" aria-label="Item Kept on Hold"></span></td>
    <td><span role="img" aria-label="26/10/2026"></span></td>
    <td><span role="img" aria-label="19:26:43"></span></td>
    <td><span role="img" aria-label="Tivim S.O"></span></td>
    <td><span role="img" aria-label="Addressee Absent[For enquiry]"></span></td>
  </tr>
</table>
</body></html>
"""


def test_deobfuscates_canvas_aria_labels_and_drops_decoys():
    adapter = IndiaPostWebAdapter()
    result = adapter.extract_table_data(OBFUSCATED_HTML, "EY672780687IN")
    events = result["events"]
    details = result["details"]
    assert len(events) == 2
    # No decoy junk leaked into any field.
    blob = str(events) + str(details)
    assert "XX" not in blob and "decoy" not in blob.lower()
    assert events[0]["status"] == "Item Booked"
    assert events[0]["location"] == "Goregaon RS SO"
    assert events[0]["date"] == "22/10/2026"
    assert details["article_type"] == "SP_INLAND_DOC"
    assert details["origin"] == "Goregaon RS SO"
    assert details["destination"] == "Tivim S.O"
    # "Item Kept on Hold" -> EXCEPTION
    assert details["status"] == "EXCEPTION"
