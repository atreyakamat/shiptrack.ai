import streamlit as st
from components.status_badge import render_status_badge
from components.timeline import render_timeline
from components.map import render_journey_map

import textwrap

def render_progress_bar(status):
    stages = ["Booked", "Dispatched", "In Transit", "Out for Delivery", "Delivered"]
    
    status_lower = status.lower()
    current_idx = 0
    if "dispatch" in status_lower: current_idx = 1
    elif "transit" in status_lower or "arrived" in status_lower or "facility" in status_lower: current_idx = 2
    elif "out" in status_lower: current_idx = 3
    elif "deliver" in status_lower: current_idx = 4
    elif "delay" in status_lower or "exception" in status_lower or "return" in status_lower: current_idx = 2
    
    icons = ["📦", "📤", "🚚", "🛵", "✅"]
    
    html_parts = ['<div class="progress-container"><div class="progress-track"></div>']
    fill_width = 0 if current_idx == 0 else (current_idx / (len(stages) - 1)) * 100
    html_parts.append(f'<div class="progress-fill" style="width: {fill_width}%;"></div><div class="progress-steps">')
    
    for i, stage in enumerate(stages):
        is_active = i == current_idx
        is_completed = i < current_idx
        
        c_class = "completed" if is_completed else "active" if is_active else ""
        l_class = "active" if (is_active or is_completed) else ""
        
        step_html = f"""
        <div class="progress-step">
            <div class="step-icon {c_class}">{icons[i]}</div>
            <div class="step-label {l_class}">{stage}</div>
        </div>
        """
        html_parts.append(textwrap.dedent(step_html).strip())
        
    html_parts.append('</div></div>')
    
    final_html = "".join(html_parts)
    st.markdown(final_html, unsafe_allow_html=True)

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
        
    tracking_no = s.get('tracking_number') or 'UNKNOWN'
    status = s.get('status') or 'Unknown'
    
    carrier = s.get('carrier') or 'India Post'
    if carrier == 'india_post':
        carrier = 'India Post'
    else:
        carrier = carrier.replace('_', ' ').title()
        
    dest = s.get('destination') or 'Not available'
    priority = s.get('priority') or 'Normal'
    if priority: priority = priority.capitalize()
    
    exp_delivery = s.get('expected_delivery') or 'Not available'
    
    latest_loc = s.get('current_location') or 'Not available'
    
    last_updated = s.get('last_updated') or 'Time unavailable'
    
    # Format Last Updated to "11 Aug 2026 · 09:07 AM"
    if last_updated != 'Time unavailable' and 'T' in last_updated:
        from datetime import datetime
        try:
            dt = datetime.strptime(last_updated[:19], "%Y-%m-%dT%H:%M:%S")
            last_updated = dt.strftime("%d %b %Y · %I:%M %p")
        except Exception:
            pass
            
    header_html = f"""
    <div>
        <h1 style="margin:0; font-size:2.5rem;">{tracking_no}</h1>
        <h3 style="margin:0; color: var(--accent-color); text-transform: uppercase;">{status.replace('_', ' ')}</h3>
        <p style="margin:0; color: var(--text-muted);">Carrier: {carrier}</p>
        <br>
        <p style="margin:0;">Destination: <strong>{dest}</strong></p>
        <p style="margin:0;">Expected Delivery: <strong>{exp_delivery}</strong></p>
        <p style="margin:0;">Priority: <strong>{priority}</strong></p>
        <br>
        <p style="margin:0; color: var(--text-muted); font-size: 0.9rem; text-transform: uppercase;">Current Location:</p>
        <p style="margin:0; font-size: 1.1rem; font-weight: 500;">{latest_loc}</p>
        <br>
        <p style="margin:0; color: var(--text-muted); font-size: 0.9rem; text-transform: uppercase;">Last Updated:</p>
        <p style="margin:0; font-size: 1.1rem; font-weight: 500;">{last_updated}</p>
    </div>
    """
    
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown(textwrap.dedent(header_html).strip(), unsafe_allow_html=True)
    with col2:
        if st.button("Refresh Status 🔄"):
            with st.spinner("Refreshing..."):
                api.refresh_shipment(sid)
                st.rerun()
                
    st.markdown("<br>", unsafe_allow_html=True)
    
    st.markdown("<h4>Journey Progress</h4>", unsafe_allow_html=True)
    render_progress_bar(status)
    
    st.markdown("<hr style='border-color: var(--border-color); margin: 2rem 0;'>", unsafe_allow_html=True)
    
    history = api.get_tracking_history(sid)
    
    # Map Section
    st.markdown("<h3>Journey Map</h3>", unsafe_allow_html=True)
    render_journey_map(history)
    
    st.markdown("<hr style='border-color: var(--border-color); margin: 2rem 0;'>", unsafe_allow_html=True)
    
    c_tl, c_ai = st.columns([3, 2])
    
    with c_tl:
        st.markdown("<h3>Tracking History</h3>", unsafe_allow_html=True)
        render_timeline(history)
        
    with c_ai:
        st.markdown("<h3>AI Insights</h3>", unsafe_allow_html=True)
        summary = api.get_ai_summary(sid)
        if not summary:
            if st.button("✨ Explain Current Status", type="primary"):
                with st.spinner("Analyzing tracking data..."):
                    api.generate_ai_summary(sid)
                    st.rerun()
            st.info("No AI insight available yet.")
        else:
            summary_text = summary.get('summary') or 'No AI insight available yet.'
            st.info(summary_text)
            st.caption("🤖 *AI-Generated Summary: This is an interpretation of known scan data, not live telemetry.*")
            
            delay_analysis = summary.get('delay_analysis')
            if delay_analysis:
                st.markdown(f"**Analysis:** {delay_analysis}")
                
            prediction = summary.get('prediction')
            if prediction:
                st.markdown(f"**Expectation:** {prediction}")
                
        # Show sync status
        st.markdown("<h4 style='margin-top: 2rem;'>Sync Status</h4>", unsafe_allow_html=True)
        st.caption(f"Last Successful: {s.get('last_successful_sync', 'Never')}")
        st.caption(f"Last Attempted: {s.get('last_attempted_sync', 'Never')}")
        if s.get('last_error'):
            st.error(f"Error: {s.get('last_error')}")
