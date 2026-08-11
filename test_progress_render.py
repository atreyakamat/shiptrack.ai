import sys
from unittest.mock import patch, MagicMock

# Mock streamlit
mock_st = MagicMock()
sys.modules['streamlit'] = mock_st

# Add frontend to path
sys.path.insert(0, 'C:/Projects/shiptrack.ai/frontend')

# Now import and test
from pages.shipment_detail import render_progress_bar

# Test with OUT_FOR_DELIVERY status
render_progress_bar('OUT_FOR_DELIVERY')

# Check the call
assert mock_st.markdown.called
args, kwargs = mock_st.markdown.call_args
html_output = args[0]

print("HTML output length:", len(html_output))
print("unsafe_allow_html:", kwargs.get("unsafe_allow_html"))

# Check for issues
print("\n--- Checks ---")
print("Contains 'progress-step':", 'progress-step' in html_output)
print("Contains 'step-icon':", 'step-icon' in html_output)
print("Contains 'step-label':", 'step-label' in html_output)
print("Contains 'completed' class:", 'class="completed"' in html_output or "class='completed'" in html_output)
print("Contains 'active' class:", 'class="active"' in html_output or "class='active'" in html_output)
print("Contains '>None<':", '>None<' in html_output)

# Check stages
print("\n--- Stage labels ---")
for stage_label, stage_icon in [("Booked", "📦"), ("Dispatched", "📤"), ("In Transit", "🚚"), ("Out for Delivery", "🛵"), ("Delivered", "✅")]:
    print(f"  Contains '{stage_label}':", stage_label in html_output)

# Print first 800 chars
print("\n--- First 800 chars of HTML ---")
print(html_output[:800])