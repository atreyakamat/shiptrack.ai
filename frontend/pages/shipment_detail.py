import streamlit as st
from components.status_badge import render_status_badge
from components.timeline import render_timeline
from components.map import render_journey_map
from frontend.utils.event_normalizer import (
    get_progress_index,
    get_progress_status_label,
    get_progress_status_icon,
    STATUS_STAGES,
)

import textwrap


def render_progress_bar(status):
    current_idx = get_progress_index(status)

    html_parts = ['<div class="progress-container"><div class="progress-track"></div>']
    fill_width = 0 if current_idx == 0 else (current_idx / (len(STATUS_STAGES) - 1)) * 100
    html_parts.append(f'<div class="progress-fill" style="width: {fill_width}%;"></div><div class="progress-steps">')

    for i, (stage_label, stage_icon) in enumerate(STATUS_STAGES):
        is_active = i == current_idx
        is_completed = i < current_idx

        c_class = "completed" if is_completed else "active" if is_active else ""
        l_class = "active" if (is_active or is_completed) else ""

        step_html = (
            f'<div class="progress-step">'
            f'<div class="step-icon {c_class}">{stage_icon}</div>'
            f'<div class="step-label {l_class}">{stage_label}</div>'
            f'</div>'
        )
        html_parts.append(step_html)

    html_parts.append('</div></div>')

    final_html = "".join(html_parts)
    st.markdown(final_html, unsafe_allow_html=True)


def _clean_display(value: str, fallback: str) -> str:
    """Clean a display value, returning fallback for None/empty/'None'."""
    if value is None:
        return fallback
    s = str(value).strip()
    if not s or s.lower() in ('none', 'null', 'undefined', 'nan'):
        return fallback
    return s


def _format_last_updated(ts: str) -> str:
    """Format ISO timestamp to '11 Aug 2026 · 09:07 AM'."""
    if not ts or ts == 'Time unavailable':
        return 'Time unavailable'
    try:
        if 'T' in ts:
            from datetime import datetime
            dt = datetime.fromisoformat(ts.replace('Z', '+00:00'))
            return dt.strftime("%d %b %Y · %I:%M %p")
    except Exception:
        pass
    return ts


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

    tracking_no = _clean_display(s.get('tracking_number'), 'UNKNOWN')
    raw_status = s.get('status') or 'Unknown'
    status = raw_status.replace('_', ' ').upper()

    carrier = _clean_display(s.get('carrier'), 'India Post')
    if carrier.lower() == 'india_post':
        carrier = 'India Post'
    else:
        carrier = carrier.replace('_', ' ').title()

    dest = _clean_display(s.get('destination'), 'Not available')
    priority = _clean_display(s.get('priority'), 'Normal')
    if priority:
        priority = priority.capitalize()

    exp_delivery = _clean_display(s.get('expected_delivery'), 'Not available')
    # Format expected delivery if it's an ISO timestamp
    if exp_delivery != 'Not available' and 'T' in exp_delivery:
        try:
            from datetime import datetime
            dt = datetime.fromisoformat(exp_delivery.replace('Z', '+00:00'))
            exp_delivery = dt.strftime("%d %b %Y")
        except Exception:
            pass

    latest_loc = _clean_display(s.get('current_location'), 'Not available')

    last_updated = _clean_display(s.get('last_updated'), 'Time unavailable')
    last_updated = _format_last_updated(last_updated)

    # Calculate transit days
    booked_at_raw = s.get('booked_at')
    transit_days_str = "Not available"
    if booked_at_raw:
        try:
            from datetime import datetime, timezone
            booked_dt = datetime.fromisoformat(booked_at_raw.replace('Z', '+00:00'))
            if s.get('status') == 'DELIVERED' and s.get('last_updated'):
                end_dt = datetime.fromisoformat(s.get('last_updated').replace('Z', '+00:00'))
            else:
                end_dt = datetime.now(timezone.utc)
            delta = end_dt - booked_dt
            days = delta.days
            if days < 0:
                days = 0
            transit_days_str = f"{days} days" if days != 1 else "1 day"
        except Exception:
            pass

    header_html = f"""
    <div>
        <h1 style="margin:0; font-size:2.5rem;">{tracking_no}</h1>
        <h3 style="margin:0; color: var(--accent-color); text-transform: uppercase;">{status}</h3>
        <p style="margin:0; color: var(--text-muted);">Carrier: {carrier}</p>
        <br>
        <p style="margin:0;">Destination: <strong>{dest}</strong></p>
        <p style="margin:0;">Expected Delivery: <strong>{exp_delivery}</strong></p>
        <p style="margin:0;">Days in Transit: <strong>{transit_days_str}</strong></p>
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
    render_progress_bar(raw_status)

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
        last_successful = _clean_display(s.get('last_successful_sync'), 'Never')
        if last_successful != 'Never' and 'T' in last_successful:
            try:
                from datetime import datetime
                dt = datetime.fromisoformat(last_successful.replace('Z', '+00:00'))
                last_successful = dt.strftime("%d %b %Y · %I:%M %p")
            except Exception:
                pass

        last_attempted = _clean_display(s.get('last_attempted_sync'), 'Never')
        if last_attempted != 'Never' and 'T' in last_attempted:
            try:
                from datetime import datetime
                dt = datetime.fromisoformat(last_attempted.replace('Z', '+00:00'))
                last_attempted = dt.strftime("%d %b %Y · %I:%M %p")
            except Exception:
                pass

        st.caption(f"Last Successful: {last_successful}")
        st.caption(f"Last Attempted: {last_attempted}")
        if s.get('last_error'):
            st.error(f"Error: {s.get('last_error')}")