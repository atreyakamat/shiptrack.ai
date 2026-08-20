import streamlit as st
import pandas as pd

def show(api):
    st.markdown("<h2>⚙️ Settings & Preferences</h2>", unsafe_allow_html=True)
    
    health = api.health_check() or {}
    
    tab1, tab2 = st.tabs(["Notification Preferences", "System Configuration"])
    
    with tab1:
        st.markdown("### Notification Preferences")
        st.markdown("Configure in-app alert triggers for your shipment lifecycle events.")
        
        preferences = api.get_notification_preferences()
        
        if not preferences:
            st.info("No notification preferences available.")
        else:
            event_order = ['SHIPMENT_ADDED', 'STATUS_CHANGED', 'OUT_FOR_DELIVERY', 'DELIVERED', 'DELAYED', 'REFRESH_FAILED']
            preferences = sorted(preferences, key=lambda x: event_order.index(x['event_type']) if x.get('event_type') in event_order else 99)
            
            col_labels = st.columns([3, 2])
            with col_labels[0]: st.markdown("**Event Trigger**")
            with col_labels[1]: st.markdown("**In-App Notification** 📱")
            
            st.markdown("<hr style='margin-top: 0; margin-bottom: 10px;'>", unsafe_allow_html=True)
            
            for pref in preferences:
                cols = st.columns([3, 2])
                event_name = pref.get('event_type', '').replace('_', ' ').title()
                
                with cols[0]:
                    st.markdown(f"<div style='margin-top: 10px;'><b>{event_name}</b></div>", unsafe_allow_html=True)
                    
                with cols[1]:
                    in_app_key = f"in_app_{pref.get('event_type')}"
                    in_app_val = st.toggle("Enabled", value=pref.get('in_app', True), key=in_app_key)
                    
                if in_app_val != pref.get('in_app'):
                    payload = {"in_app": in_app_val, "whatsapp": False, "email": False}
                    update_res = api.update_notification_preference(pref.get('event_type'), payload)
                    if update_res:
                        st.toast(f"Updated preferences for {event_name}")
                        st.rerun()
                        
                st.markdown("<hr style='margin: 5px 0;'>", unsafe_allow_html=True)

            st.caption("ℹ️ *Note: In-App notifications are active. External WhatsApp and Email channels are deferred.*")

    with tab2:
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("### 🌐 Tracking Configuration")
            st.text_input("Configured Tracking Provider", value=health.get('tracking_provider', 'mock').upper(), disabled=True)
            st.checkbox("Demo Mode Active", value=health.get('demo_mode', True), disabled=True)
            
            st.markdown("### 🧠 AI Engine")
            st.text_input("AI Provider", value=health.get('ai_provider', 'mock').title(), disabled=True)
            st.caption("Heuristic rule-based interpretation grounded in structured scan history.")
            
        with c2:
            st.markdown("### 📷 OCR Engine")
            st.text_input("OCR Engine", value="EasyOCR (Local CPU/GPU)", disabled=True)
            st.caption("Extracts tracking candidates locally without external cloud telemetry.")
            
            st.markdown("### 🗄️ Database & Environment")
            st.text_input("API Version", value=health.get('version', '1.0.0'), disabled=True)
            
    st.markdown("<hr style='border-color: var(--border-color);'>", unsafe_allow_html=True)
    st.markdown("""
        <div style="text-align: center; color: var(--text-muted); font-size: 0.85rem;">
            ShipTrack AI Application<br>
            Version 1.0.0
        </div>
    """, unsafe_allow_html=True)
