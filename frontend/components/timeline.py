import streamlit as st
import textwrap
from frontend.utils.event_normalizer import normalize_tracking_events, get_status_icon


def render_timeline(events):
    if not events:
        st.info("No tracking history available.")
        return

    normalized_events = normalize_tracking_events(events)

    html_parts = ['<div class="timeline">']

    for event in normalized_events:
        is_latest = event.get('is_latest', False)
        active_class = "active" if is_latest else ""
        opacity = "1" if is_latest else "0.7"

        date_str = event['date_display']
        time_str = event['time_display']
        status = event['status']
        location = event['location']
        description = event['description']
        icon = event['icon']

        location_text = f"{icon} {location}" if location and location != 'Location unavailable' else ""
        desc_html = f'<div class="timeline-desc">{description}</div>' if description else ""
        title_right = f'<span style="color: var(--text-muted); font-size: 0.8rem; font-weight: normal;">{location_text}</span>' if location_text else ""

        event_html = f"""
        <div class="timeline-event" style="opacity: {opacity};">
            <div class="timeline-time">
                <div style="font-weight: 600; color: var(--text-primary);">{date_str}</div>
                <div style="color: var(--text-muted); font-size: 0.8rem;">{time_str}</div>
            </div>
            <div class="timeline-marker {active_class}"></div>
            <div class="timeline-content">
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

    final_html = "\n".join(html_parts)
    st.markdown(final_html, unsafe_allow_html=True)