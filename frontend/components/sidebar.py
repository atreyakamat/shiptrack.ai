import streamlit as st

def render_sidebar():
    with st.sidebar:
        st.markdown(
            """
            <div style="margin-bottom: 2rem;">
                <h1 style="color: var(--accent-color); margin-bottom: 0;">📦 ShipTrack AI</h1>
                <p style="color: var(--text-muted); font-size: 0.85rem; margin-top: 0;">Track smarter. Understand deliveries.</p>
            </div>
            """, 
            unsafe_allow_html=True
        )

        nav_items = [
            {"id": "dashboard", "icon": "📊", "label": "Dashboard"},
            {"id": "shipments", "icon": "📋", "label": "Shipments"},
            {"id": "add_shipment", "icon": "➕", "label": "Add Shipment"},
            {"id": "ocr_scanner", "icon": "📷", "label": "OCR Scanner"},
            {"id": "analytics", "icon": "📈", "label": "Analytics"},
            {"id": "ai_insights", "icon": "🧠", "label": "AI Insights"},
            {"id": "notifications", "icon": "🔔", "label": "Notifications", "badge": "3"},
            {"id": "settings", "icon": "⚙️", "label": "Settings"},
        ]

        current_page = st.session_state.get('current_page', 'dashboard')

        for item in nav_items:
            # We use st.button for navigation, styled via CSS
            is_active = current_page == item['id']
            # We create a container that looks like a link
            btn_label = f"{item['icon']} {item['label']}"
            if 'badge' in item and item['badge']:
                btn_label += f" ({item['badge']})"
                
            # Use Streamlit buttons as navigation (they will reload the app)
            if st.button(btn_label, key=f"nav_{item['id']}", use_container_width=True, type="primary" if is_active else "secondary"):
                st.session_state['current_page'] = item['id']
                st.rerun()

        if st.button("🚪 Log Out", key="nav_logout", use_container_width=True, type="secondary"):
            if 'auth_token' in st.session_state:
                del st.session_state['auth_token']
            st.rerun()

        st.markdown("<hr style='border-color: var(--border-color); margin: 1.5rem 0;'>", unsafe_allow_html=True)
        
        # Check health/demo status from session state (populated in main app)
        health_status = st.session_state.get('api_health', {})
        is_demo = health_status.get('demo_mode', False)
        status_color = "var(--success)" if health_status else "var(--error)"
        
        st.markdown(
            f"""
            <div style="font-size: 0.8rem; color: var(--text-muted); margin-bottom: 1rem;">
                <span style="display: inline-block; width: 8px; height: 8px; border-radius: 50%; background-color: {status_color}; margin-right: 5px;"></span>
                API Status: {'Demo Mode' if is_demo else 'Connected' if health_status else 'Disconnected'}
            </div>
            <div style="font-size: 0.75rem; color: var(--text-muted);">
                Built by Atreya Kamat<br>
                v1.0.0
            </div>
            """,
            unsafe_allow_html=True
        )
