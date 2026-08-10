import streamlit as st
import os

# 1. Page Config (Must be first)
st.set_page_config(
    page_title='ShipTrack AI',
    page_icon='📦',
    layout='wide',
    initial_sidebar_state='expanded'
)

# 2. Load CSS
css_path = os.path.join(os.path.dirname(__file__), 'styles', 'main.css')
if os.path.exists(css_path):
    with open(css_path) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# 3. Imports
from api_client import ShipTrackAPI
from components.sidebar import render_sidebar
from pages import (
    dashboard,
    shipments,
    shipment_detail,
    add_shipment,
    ocr_scanner,
    analytics,
    ai_insights,
    notifications,
    settings
)

# 4. Initialize State
if 'current_page' not in st.session_state:
    st.session_state['current_page'] = 'dashboard'

# Initialize API Client
@st.cache_resource
def get_api():
    return ShipTrackAPI()

api = get_api()

# Fetch health status on load
if 'api_health' not in st.session_state:
    st.session_state['api_health'] = api.health_check()

if 'auth_token' not in st.session_state:
    from pages import login
    login.show(api)
else:
    # Inject token into API client
    api.set_token(st.session_state.auth_token)
    
    # 5. Render Sidebar
    render_sidebar()
    
    # 6. Page Routing
    current = st.session_state['current_page']
    
    if current == 'dashboard':
        dashboard.show(api)
    elif current == 'shipments':
        shipments.show(api)
    elif current == 'shipment_detail':
        shipment_detail.show(api)
    elif current == 'add_shipment':
        add_shipment.show(api)
    elif current == 'ocr_scanner':
        ocr_scanner.show(api)
    elif current == 'analytics':
        analytics.show(api)
    elif current == 'ai_insights':
        ai_insights.show(api)
    elif current == 'notifications':
        notifications.show(api)
    elif current == 'settings':
        settings.show(api)
    else:
        dashboard.show(api)
