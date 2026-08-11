import sys
from io import StringIO
from unittest.mock import patch, MagicMock

# Mock streamlit
mock_st = MagicMock()
sys.modules['streamlit'] = mock_st

# Now import and test
from frontend.components.timeline import render_timeline

events = [
    {
        'event_timestamp': '2026-08-11T09:07:44',
        'status': 'Out for Delivery',
        'location': 'Bambavada S.O.',
        'description': 'Item Out for Delivery'
    },
    {
        'event_timestamp': '2026-08-11T08:13:44',
        'status': 'Item Received',
        'location': 'Bambavada S.O.',
        'description': None
    },
    {
        'event_timestamp': '2026-08-11T08:06:44',
        'status': 'Bag Received',
        'location': 'Bambavada S.O.',
        'description': ''
    }
]

render_timeline(events)

# Check the call
assert mock_st.markdown.called
args, kwargs = mock_st.markdown.call_args
html_output = args[0]

print("HTML output length:", len(html_output))
print("unsafe_allow_html:", kwargs.get("unsafe_allow_html"))

# Check for issues
print("\n--- Checks ---")
print("Contains 'timeline-event':", 'timeline-event' in html_output)
print("Contains 'timeline-desc':", 'timeline-desc' in html_output)
print("Contains '11 Aug 2026':", '11 Aug 2026' in html_output)
print("Contains '09:07 AM':", '09:07 AM' in html_output)
print("Contains '08:13 AM':", '08:13 AM' in html_output)
print("Contains '08:06 AM':", '08:06 AM' in html_output)
print("Contains '>None<':", '>None<' in html_output)
print("Contains 'None' as text:", '>None<' in html_output or '>None ' in html_output or ' None<' in html_output)

# Check raw HTML is not visible
print("\n--- Raw HTML check ---")
# The HTML should be rendered, not shown as text
# So we should NOT see literal "<div class=" in the output as text
# But we SHOULD see it as actual HTML tags
print("Has proper HTML structure:", html_output.startswith('<div class="timeline">'))

# Print first 500 chars
print("\n--- First 500 chars of HTML ---")
print(html_output[:500])