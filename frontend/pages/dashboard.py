import streamlit as st
from components.metric_card import render_metric_card
from components.shipment_card import render_shipment_row
from components.charts import status_distribution_chart, shipments_over_time_chart
from datetime import datetime

def show(api):
    st.markdown("<h2>Good afternoon, Atreya</h2>", unsafe_allow_html=True)
    
    health = st.session_state.get('api_health', {})
        
    st.markdown("<p class='text-muted'>Your shipment overview</p>", unsafe_allow_html=True)
    
    # Metrics
    analytics_data = api.get_analytics()
    if not analytics_data:
        analytics_data = {}
    stats = analytics_data.get('overview', {
        'total': 0, 'in_transit': 0, 'out_for_delivery': 0,
        'delivered': 0, 'delayed': 0
    })
        
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1: render_metric_card("Total Shipments", stats.get('total', 0), "📦")
    with c2: render_metric_card("In Transit", stats.get('in_transit', 0), "🚚", "var(--status-transit)")
    with c3: render_metric_card("Out for Delivery", stats.get('out_for_delivery', 0), "🛵", "var(--status-out)")
    with c4: render_metric_card("Delivered", stats.get('delivered', 0), "✅", "var(--status-delivered)")
    with c5: render_metric_card("Delayed / Attention", stats.get('delayed', 0), "⚠️", "var(--status-delayed)")
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    shipments = api.get_shipments() or []
    
    # Needs Attention Section
    delayed_shipments = [s for s in shipments if s.get('status') in ['DELAYED', 'EXCEPTION']]
    if delayed_shipments:
        st.markdown("<h4 style='color: var(--status-delayed);'>⚠️ Shipments Needing Attention</h4>", unsafe_allow_html=True)
        for s in delayed_shipments[:5]:
            col_card, col_acts = st.columns([5, 1])
            with col_card:
                render_shipment_row(s)
            with col_acts:
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("View", key=f"view_att_{s.get('id')}", use_container_width=True):
                    st.session_state['current_shipment_id'] = s.get('id')
                    st.session_state['current_page'] = 'shipment_detail'
                    st.rerun()
        st.markdown("<br>", unsafe_allow_html=True)
    
    # Charts Row
    ch1, ch2 = st.columns([1, 2])
    
    with ch1:
        st.markdown("<h4>Status Distribution</h4>", unsafe_allow_html=True)
        by_status = analytics_data.get('by_status', [])
        fig_donut = status_distribution_chart(by_status)
        st.plotly_chart(fig_donut, use_container_width=True, config={'displayModeBar': False})
        
    with ch2:
        st.markdown("<h4>Shipments Over Time</h4>", unsafe_allow_html=True)
        over_time = analytics_data.get('shipments_over_time', [])
        fig_area = shipments_over_time_chart(over_time)
        st.plotly_chart(fig_area, use_container_width=True, config={'displayModeBar': False})

    # Recent Shipments, Stale Shipments & Recent Activity
    col_left, col_right = st.columns([3, 2])
    
    with col_left:
        st.markdown("<h4>Recent Shipment Updates</h4>", unsafe_allow_html=True)
        if not shipments:
            st.info("No recent shipments found.")
        else:
            for s in shipments[:8]:
                col_card, col_acts = st.columns([4, 1])
                with col_card:
                    render_shipment_row(s)
                with col_acts:
                    st.markdown("<br>", unsafe_allow_html=True)
                    if st.button("View", key=f"view_{s.get('id')}", use_container_width=True):
                        st.session_state['current_shipment_id'] = s.get('id')
                        st.session_state['current_page'] = 'shipment_detail'
                        st.rerun()
                    if st.button("Refresh", key=f"refresh_{s.get('id')}", use_container_width=True):
                        with st.spinner("Refreshing..."):
                            res = api.refresh_shipment(s.get('id'))
                            if res:
                                st.toast(f"Shipment {s.get('tracking_number')} updated successfully!", icon="✅")
                                st.rerun()
                                
        # Stale Shipments
        stale = analytics_data.get('stale_shipments', [])
        if stale:
            st.markdown("<h4 style='color: var(--status-delayed); margin-top: 2rem;'>⚠️ Stale Shipments (No update > 7 days)</h4>", unsafe_allow_html=True)
            for s in stale[:5]:
                tracking = s.get('tracking_number', 'Unknown')
                status = s.get('status', 'Unknown')
                last_updated = s.get('last_updated', 'Unknown')
                if 'T' in last_updated:
                    try:
                        from datetime import datetime
                        dt = datetime.fromisoformat(last_updated.replace('Z', '+00:00'))
                        last_updated = dt.strftime("%d %b %Y · %I:%M %p")
                    except Exception:
                        pass
                st.markdown(f"- **{tracking}** — *{status}* — Last updated: {last_updated}")
                
    with col_right:
        st.markdown("<h4>Recent Tracking Activity</h4>", unsafe_allow_html=True)
        activity = analytics_data.get('recent_activity', [])
        if not activity:
            st.info("No recent tracking activity.")
        else:
            for act in activity[:10]:
                tracking_no = act.get('tracking_number', 'Unknown')
                status = act.get('status', 'Update').replace('_', ' ').title()
                location = act.get('location', 'Unknown Location')
                time_str = act.get('event_timestamp') or act.get('created_at') or ''
                if 'T' in time_str:
                    try:
                        from datetime import datetime
                        dt = datetime.fromisoformat(time_str.replace('Z', '+00:00'))
                        time_str = dt.strftime("%d %b %Y · %I:%M %p")
                    except Exception:
                        pass
                st.markdown(f"""
                <div style='padding: 0.75rem; border-left: 3px solid var(--accent-color); background: rgba(255,255,255,0.02); margin-bottom: 0.5rem;'>
                    <span style='font-size: 0.8rem; color: var(--text-muted);'>{time_str}</span><br>
                    <strong>{tracking_no}</strong> — <span style='color: var(--accent-color);'>{status}</span><br>
                    <span style='font-size: 0.9rem;'>At {location}</span>
                </div>
                """, unsafe_allow_html=True)

    st.markdown("<hr style='border-color: var(--border-color);'>", unsafe_allow_html=True)
    col_sync, col_btn = st.columns([4, 1])
    with col_sync:
        st.markdown(f"<span class='text-muted'>Last sync: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</span>", unsafe_allow_html=True)
    with col_btn:
        if st.button("Refresh All 🔄", use_container_width=True):
            with st.spinner("Refreshing active shipments..."):
                res = api.refresh_all()
                if res:
                    st.toast("All active shipments updated!", icon="✅")
                    st.rerun()
