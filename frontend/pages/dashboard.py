import streamlit as st
from components.metric_card import render_metric_card
from components.shipment_card import render_shipment_row
from components.charts import status_distribution_chart, shipments_over_time_chart
from datetime import datetime

def show(api):
    st.markdown("<h2>Good afternoon, Atreya</h2>", unsafe_allow_html=True)
    
    health = st.session_state.get('api_health', {})
    if health.get('demo_mode') or health.get('tracking_provider') == 'mock':
        st.warning("⚠️ **DEMO MODE ACTIVE** - Tracking data is simulated. Real Carrier API connections are disabled or unavailable.")
        
    st.markdown("<p class='text-muted'>Your shipment overview</p>", unsafe_allow_html=True)
    
    # Metrics
    stats = api.get_analytics()
    if not stats:
        stats = {
            'total': 0, 'in_transit': 0, 'out_for_delivery': 0,
            'delivered': 0, 'delayed': 0
        }
        
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1: render_metric_card("Total Shipments", stats.get('total', 0), "📦")
    with c2: render_metric_card("In Transit", stats.get('in_transit', 0), "🚚", "var(--status-transit)")
    with c3: render_metric_card("Out for Delivery", stats.get('out_for_delivery', 0), "🛵", "var(--status-out)")
    with c4: render_metric_card("Delivered", stats.get('delivered', 0), "✅", "var(--status-delivered)")
    with c5: render_metric_card("Delayed", stats.get('delayed', 0), "⚠️", "var(--status-delayed)")
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Charts Row
    ch1, ch2 = st.columns([1, 2])
    shipments = api.get_shipments() or []
    
    with ch1:
        st.markdown("<h4>Status Distribution</h4>", unsafe_allow_html=True)
        fig_donut = status_distribution_chart(shipments)
        st.plotly_chart(fig_donut, use_container_width=True, config={'displayModeBar': False})
        
    with ch2:
        st.markdown("<h4>Shipments Over Time</h4>", unsafe_allow_html=True)
        fig_area = shipments_over_time_chart(shipments)
        st.plotly_chart(fig_area, use_container_width=True, config={'displayModeBar': False})

    # Recent Shipments
    st.markdown("<h4>Recent Shipments</h4>", unsafe_allow_html=True)
    if not shipments:
        st.info("No recent shipments found.")
    else:
        for s in shipments[:10]:
            col_card, col_acts = st.columns([5, 1])
            with col_card:
                render_shipment_row(s)
            with col_acts:
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("View", key=f"view_{s.get('id', s.get('tracking_number'))}", use_container_width=True):
                    st.session_state['current_shipment_id'] = s.get('id', s.get('tracking_number'))
                    st.session_state['current_page'] = 'shipment_detail'
                    st.rerun()
                if st.button("Refresh", key=f"refresh_{s.get('id', s.get('tracking_number'))}", use_container_width=True):
                    with st.spinner("Refreshing..."):
                        res = api.refresh_shipment(s.get('id', s.get('tracking_number')))
                        if res:
                            st.toast(f"Shipment {s.get('tracking_number')} updated successfully!", icon="✅")
                            st.rerun()
                if st.button("Archive", key=f"archive_{s.get('id', s.get('tracking_number'))}", use_container_width=True):
                    api.archive_shipment(s.get('id', s.get('tracking_number')))
                    st.toast(f"Shipment archived.", icon="📦")
                    st.rerun()

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
