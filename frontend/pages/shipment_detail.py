import streamlit as st
from components.status_badge import render_status_badge
from components.timeline import render_timeline

def render_progress_bar(status):
    stages = ["Booked", "Dispatched", "In Transit", "Out for Delivery", "Delivered"]
    
    status_lower = status.lower()
    current_idx = 0
    if "dispatch" in status_lower: current_idx = 1
    elif "transit" in status_lower: current_idx = 2
    elif "out" in status_lower: current_idx = 3
    elif "deliver" in status_lower: current_idx = 4
    elif "delay" in status_lower: current_idx = 2
    
    icons = ["📦", "📤", "🚚", "🛵", "✅"]
    
    html = '<div class="progress-container"><div class="progress-track"></div>'
    fill_width = 0 if current_idx == 0 else (current_idx / (len(stages) - 1)) * 100
    html += f'<div class="progress-fill" style="width: {fill_width}%;"></div><div class="progress-steps">'
    
    for i, stage in enumerate(stages):
        is_active = i == current_idx
        is_completed = i < current_idx
        
        c_class = "completed" if is_completed else "active" if is_active else ""
        l_class = "active" if (is_active or is_completed) else ""
        
        html += f"""
        <div class="progress-step">
            <div class="step-icon {c_class}">{icons[i]}</div>
            <div class="step-label {l_class}">{stage}</div>
        </div>
        """
    html += '</div></div>'
    st.markdown(html, unsafe_allow_html=True)

def show(api):
    if st.button("← Back to Shipments"):
        st.session_state['current_page'] = 'shipments'
        st.rerun()
        
    sid = st.session_state.get('current_shipment_id')
    if not sid:
        st.error("No shipment selected.")
        return
        
    s = api.get_shipment(sid)
    if not s:
        st.error("Could not load shipment details.")
        return
        
    tracking_no = s.get('tracking_number', 'UNKNOWN')
    status = s.get('status', 'Unknown')
    carrier = s.get('carrier', 'Unknown')
    
    st.markdown(f"""
        <div style="display:flex; align-items:center; gap: 1rem; margin-bottom: 1rem;">
            <h1 style="margin:0; font-size:2rem;">{tracking_no}</h1>
            {render_status_badge(status)}
        </div>
        <p class="text-muted" style="margin-top:-0.5rem; margin-bottom:2rem;">Carrier: {carrier}</p>
    """, unsafe_allow_html=True)
    
    render_progress_bar(status)
    
    # Info Grid
    st.markdown("<h3>Shipment Details</h3>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f"**Origin:** {s.get('origin', 'N/A')}")
        st.markdown(f"**Destination:** {s.get('destination', 'N/A')}")
        st.markdown(f"**Current Location:** {s.get('current_location', 'N/A')}")
    with col2:
        st.markdown(f"**Booked Date:** {s.get('booked_date', 'N/A')}")
        st.markdown(f"**Expected Delivery:** {s.get('expected_delivery', 'N/A')}")
        st.markdown(f"**Last Updated:** {s.get('last_updated', 'N/A')}")
    with col3:
        st.markdown(f"**Category:** {s.get('category', 'General')}")
        st.markdown(f"**Priority:** {s.get('priority', 'Normal')}")
        st.markdown(f"**Description:** {s.get('description', 'N/A')}")
        
    st.markdown("<hr style='border-color: var(--border-color);'>", unsafe_allow_html=True)
    
    c_tl, c_ai = st.columns([3, 2])
    
    with c_tl:
        st.markdown("<h3>Tracking Timeline</h3>", unsafe_allow_html=True)
        history = api.get_tracking_history(sid)
        render_timeline(history)
        
    with c_ai:
        st.markdown("<h3>AI Insights</h3>", unsafe_allow_html=True)
        summary = api.get_ai_summary(sid)
        if not summary:
            if st.button("✨ Generate AI Summary", type="primary"):
                with st.spinner("Analyzing..."):
                    api.generate_ai_summary(sid)
                    st.rerun()
        else:
            # We must use summary.get('summary') since ai_service sets 'summary', not 'text'
            st.info(summary.get('summary', 'No summary available.'))
            st.caption("🤖 *AI-Generated Summary: This is an interpretation of structured tracking data, not an official carrier statement.*")
            
            delay_analysis = summary.get('delay_analysis')
            if delay_analysis:
                st.markdown(f"**Delay Analysis:** {delay_analysis}")
                
            prediction = summary.get('prediction')
            if prediction:
                st.markdown(f"**Prediction:** {prediction}")
            
    if st.button("Refresh Status 🔄"):
        api.refresh_shipment(sid)
        st.rerun()
