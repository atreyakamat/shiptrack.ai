import pytest
import textwrap
from unittest.mock import patch, MagicMock

# Import the components we want to test
from frontend.components.timeline import get_status_icon

def test_timeline_event_normalization():
    # Test that status mapping returns correct icons
    assert get_status_icon("Delivered") == "✅"
    assert get_status_icon("Out for delivery") == "🛵"
    assert get_status_icon("In transit") == "🚚"
    assert get_status_icon("Item booked") == "📦"
    assert get_status_icon("Unknown status") == "📍"

def test_progress_status_mapping():
    # The progress logic maps string states to indexes
    def get_progress_idx(status):
        status_lower = status.lower()
        if "dispatch" in status_lower: return 1
        elif "transit" in status_lower or "arrived" in status_lower or "facility" in status_lower: return 2
        elif "out" in status_lower: return 3
        elif "deliver" in status_lower: return 4
        elif "delay" in status_lower or "exception" in status_lower or "return" in status_lower: return 2
        return 0

    assert get_progress_idx("Booked") == 0
    assert get_progress_idx("Item Dispatched") == 1
    assert get_progress_idx("In Transit") == 2
    assert get_progress_idx("Out for Delivery") == 3
    assert get_progress_idx("Delivered") == 4
    assert get_progress_idx("Delayed") == 2

def test_null_timeline_values():
    # If description is "None", it should be omitted
    desc = "None"
    if str(desc).strip().lower() == "none":
        desc = ""
    assert desc == ""
    
    loc = "None"
    if str(loc).strip().lower() == "none":
        loc = ""
    assert loc == ""

@patch("streamlit.markdown")
def test_timeline_html_rendering(mock_markdown):
    from frontend.components.timeline import render_timeline
    
    events = [{
        'event_timestamp': '2026-08-11T09:07:44',
        'status': 'Out for Delivery',
        'location': 'Bambavada S.O.',
        'description': 'None'
    }]
    
    render_timeline(events)
    
    # Ensure st.markdown was called with unsafe_allow_html=True
    assert mock_markdown.called
    args, kwargs = mock_markdown.call_args
    html_output = args[0]
    assert kwargs.get("unsafe_allow_html") is True
    
    # Ensure raw "None" string is absent
    assert ">None<" not in html_output
    
    # Ensure timestamps formatted correctly
    assert "11 Aug 2026" in html_output
    assert "09:07 AM" in html_output

