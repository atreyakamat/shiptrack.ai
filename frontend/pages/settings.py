import streamlit as st
import pandas as pd

def show(api):
    st.markdown("<h2>⚙️ Settings & Preferences</h2>", unsafe_allow_html=True)
    
    health = api.health_check() or {}
    
    tab1, tab2 = st.tabs(["Notification Preferences", "System Configuration"])
    
    with tab1:
        st.markdown("### Notification Engine")
        st.markdown("Configure how and when you receive alerts.")
        
        response = api.client.get(f"{api.base_url}/notifications/preferences")
        
        if response.status_code != 200:
            st.error("Failed to load notification preferences.")
        else:
            preferences = response.json()
            event_order = ['SHIPMENT_ADDED', 'STATUS_CHANGED', 'OUT_FOR_DELIVERY', 'DELIVERED', 'DELAYED', 'REFRESH_FAILED']
            preferences = sorted(preferences, key=lambda x: event_order.index(x['event_type']) if x['event_type'] in event_order else 99)
            
            col_labels = st.columns([3, 2, 2, 2])
            with col_labels[0]: st.markdown("**Event Type**")
            with col_labels[1]: st.markdown("**In-App** 📱")
            with col_labels[2]: st.markdown("**WhatsApp** 💬")
            with col_labels[3]: st.markdown("**Email** ✉️")
            
            st.markdown("<hr style='margin-top: 0; margin-bottom: 10px;'>", unsafe_allow_html=True)
            
            for pref in preferences:
                cols = st.columns([3, 2, 2, 2])
                event_name = pref['event_type'].replace('_', ' ').title()
                
                with cols[0]:
                    st.markdown(f"<div style='margin-top: 10px;'><b>{event_name}</b></div>", unsafe_allow_html=True)
                    
                with cols[1]:
                    in_app_key = f"in_app_{pref['event_type']}"
                    in_app_val = st.toggle(" ", value=pref['in_app'], key=in_app_key)
                    
                with cols[2]:
                    wa_key = f"wa_{pref['event_type']}"
                    wa_val = st.toggle(" ", value=pref['whatsapp'], key=wa_key)
                    
                with cols[3]:
                    email_key = f"email_{pref['event_type']}"
                    email_val = st.toggle(" ", value=pref['email'], key=email_key)
                    
                if in_app_val != pref['in_app'] or wa_val != pref['whatsapp'] or email_val != pref['email']:
                    payload = {"in_app": in_app_val, "whatsapp": wa_val, "email": email_val}
                    update_res = api.client.put(f"{api.base_url}/notifications/preferences/{pref['event_type']}", json=payload)
                    if update_res.status_code == 200:
                        st.toast(f"Updated preferences for {event_name}")
                        st.rerun()
                    else:
                        st.toast(f"Failed to update {event_name}", icon="❌")
                        
                st.markdown("<hr style='margin: 5px 0;'>", unsafe_allow_html=True)

            st.info("WhatsApp and Email integrations are currently running in **Mock Mode**. They will output payloads to the backend logs instead of connecting to real APIs.")

    with tab2:
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("### 🌐 Tracking Configuration")
            st.text_input("Default Provider", value="India Post", disabled=True)
            st.checkbox("Enable Demo Mode", value=health.get('demo_mode', False), disabled=True)
            
            st.markdown("### 🧠 AI Configuration")
            st.selectbox("LLM Provider", ["OpenAI", "Gemini", "Anthropic"], index=1)
            st.selectbox("Model", ["gemini-1.5-pro", "gemini-1.5-flash"], index=0)
            
            st.markdown("### 📷 OCR Engine")
            st.selectbox("Engine", ["Tesseract", "Google Cloud Vision", "AWS Textract"], index=1)
            
        with c2:
            st.markdown("### 💬 WhatsApp Integration")
            st.info("Status: Configured" if health.get('whatsapp_configured') else "Status: Not Configured")
            st.text_input("WhatsApp API Token", type="password")
            
            st.markdown("### 🔄 Scheduler")
            st.checkbox("Enable Auto-Refresh", value=True)
            st.selectbox("Refresh Interval", ["15 mins", "30 mins", "1 hour", "6 hours"], index=2)
            
            st.markdown("### 🗄️ System")
            st.text_input("Database Type", value="PostgreSQL", disabled=True)
            
    st.markdown("<hr style='border-color: var(--border-color);'>", unsafe_allow_html=True)
    st.markdown("""
        <div style="text-align: center; color: var(--text-muted); font-size: 0.85rem;">
            ShipTrack AI Application<br>
            Version 1.0.0<br>
            Developer: Atreya Kamat
        </div>
    """, unsafe_allow_html=True)
