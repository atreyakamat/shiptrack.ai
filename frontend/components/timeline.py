import streamlit as st

def get_status_icon(status):
    s = status.lower()
    if 'delivered' in s: return "✅"
    if 'out for delivery' in s: return "🛵"
    if 'transit' in s or 'dispatched' in s: return "🚚"
    if 'booked' in s or 'bagged' in s: return "📦"
    if 'delayed' in s or 'exception' in s: return "⚠️"
    return "📍"

import textwrap

def render_timeline(events):
    if not events:
        st.info("No tracking history available.")
        return

    html_parts = ['<div class="timeline" style="padding: 10px 0;">']
    
    for i, event in enumerate(events):
        is_latest = (i == 0)
        active_class = "active" if is_latest else ""
        
        ts = event.get('event_timestamp') or ''
        date_str = ""
        time_str = ""
        
        if ts and 'T' in ts:
            from datetime import datetime
            try:
                dt = datetime.strptime(ts[:19], "%Y-%m-%dT%H:%M:%S")
                date_str = dt.strftime("%d %b %Y")
                time_str = dt.strftime("%I:%M %p")
            except:
                parts = ts.split('T', 1)
                date_str = parts[0]
                if len(parts) > 1:
                    time_str = parts[1][:5]
        elif ts:
            date_str = ts
            
        status = event.get('status') or 'Tracking Update'
        location = event.get('location') or ''
        desc = event.get('description') or ''
        
        # Omit literal string "None"
        if str(desc).strip().lower() == "none":
            desc = ""
        if str(location).strip().lower() == "none":
            location = ""
            
        icon = get_status_icon(status)
        location_text = f"{icon} {location}" if location else ""
        
        # Add opacity to older events for visual hierarchy
        opacity = "1" if is_latest else "0.7"
        
        desc_html = f'<div class="timeline-desc" style="margin-top: 6px; line-height: 1.4;">{desc}</div>' if desc else ""
        title_right = f'<span style="color: var(--text-muted); font-size: 0.8rem; font-weight: normal;">{location_text}</span>' if location_text else ""
        
        event_html = f"""
        <div class="timeline-event" style="opacity: {opacity};">
            <div class="timeline-time" style="flex: 0 0 100px; padding-right: 20px;">
                <div style="font-weight: 600; color: var(--text-primary);">{date_str}</div>
                <div style="color: var(--text-muted); font-size: 0.8rem;">{time_str}</div>
            </div>
            <div class="timeline-marker {active_class}" style="display: flex; align-items: center; justify-content: center; font-size: 0.7rem;">{icon if is_latest else ""}</div>
            <div class="timeline-content" style="margin-left: 30px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
                <div class="timeline-title" style="display: flex; justify-content: space-between;">
                    <span>{status}</span>
                    {title_right}
                </div>
                {desc_html}
            </div>
        </div>
        """
        html_parts.append(textwrap.dedent(event_html).strip())
        
    html_parts.append('</div>')
    
    css_content = """
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
    """
    
    final_html = "\\n".join(html_parts) + css_content
    st.markdown(final_html, unsafe_allow_html=True)
