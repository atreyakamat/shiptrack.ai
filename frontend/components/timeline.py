import streamlit as st

def get_status_icon(status):
    s = status.lower()
    if 'delivered' in s: return "✅"
    if 'out for delivery' in s: return "🛵"
    if 'transit' in s or 'dispatched' in s: return "🚚"
    if 'booked' in s or 'bagged' in s: return "📦"
    if 'delayed' in s or 'exception' in s: return "⚠️"
    return "📍"

def render_timeline(events):
    if not events:
        st.info("No tracking history available.")
        return

    html_content = '<div class="timeline" style="padding: 10px 0;">'
    
    for i, event in enumerate(events):
        is_latest = (i == 0)
        active_class = "active" if is_latest else ""
        
        date_str = event.get('timestamp', '')
        time_str = ''
        if date_str:
            if ' ' in date_str:
                date_str, time_str = date_str.split(' ', 1)
            elif 'T' in date_str:
                date_str, time_str = date_str.split('T', 1)
                time_str = time_str[:5] # just HH:MM
            else:
                time_str = ''
        else:
            date_str = 'Unknown Date'
            
        status = event.get('status', 'Unknown')
        location = event.get('location', '')
        desc = event.get('description', '')
        icon = get_status_icon(status)
        location_text = f"{icon} {location}" if location else f"{icon} Unknown Location"
        
        # Add opacity to older events for visual hierarchy
        opacity = "1" if is_latest else "0.7"
        
        html_content += f"""
        <div class="timeline-event" style="opacity: {opacity};">
            <div class="timeline-time" style="flex: 0 0 100px; padding-right: 20px;">
                <div style="font-weight: 600; color: var(--text-primary);">{date_str}</div>
                <div style="color: var(--text-muted); font-size: 0.8rem;">{time_str}</div>
            </div>
            
            <div class="timeline-marker {active_class}" style="display: flex; align-items: center; justify-content: center; font-size: 0.7rem;">
                {icon if is_latest else ''}
            </div>
            
            <div class="timeline-content" style="margin-left: 30px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
                <div class="timeline-title" style="display: flex; justify-content: space-between;">
                    <span>{status}</span>
                    <span style="color: var(--text-muted); font-size: 0.8rem; font-weight: normal;">
                        {location_text}
                    </span>
                </div>
                <div class="timeline-desc" style="margin-top: 6px; line-height: 1.4;">{desc}</div>
            </div>
        </div>
        """
        
    html_content += '</div>'
    
    # Custom CSS for the timeline line to ensure it looks connected
    st.markdown("""
    <style>
    .timeline::before {
        left: 106px !important;
        background: linear-gradient(to bottom, var(--accent-color) 0%, var(--border-color) 20%) !important;
    }
    .timeline-marker {
        left: 100px !important;
        width: 16px !important;
        height: 16px !important;
        margin-top: 2px !important;
    }
    .timeline-marker.active {
        width: 20px !important;
        height: 20px !important;
        left: 98px !important;
        margin-top: 0 !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    st.markdown(html_content, unsafe_allow_html=True)
