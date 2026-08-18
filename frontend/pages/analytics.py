import streamlit as st
from components.metric_card import render_metric_card
from components.charts import (
    status_distribution_chart, 
    shipments_over_time_chart,
    delivery_time_distribution_chart,
    delivery_time_by_carrier_chart,
    delivery_time_by_location_chart,
    location_frequency_chart,
    recent_activity_chart
)

def show(api):
    st.markdown("<h2>Analytics</h2>", unsafe_allow_html=True)
    
    # Filters
    c1, c2, c3, c4 = st.columns([2, 2, 2, 1])
    with c1: st.selectbox("Date Range", ["Last 6 Months", "Last Year", "All Time"], key="analytics_date_range")
    with c2: st.selectbox("Carrier", ["All", "India Post", "Delhivery"], key="analytics_carrier")
    with c3: st.selectbox("Category", ["All", "General", "Documents"], key="analytics_category")
    with c4:
        st.markdown("<br>", unsafe_allow_html=True)
        csv_data = api.export_csv()
        if csv_data:
            st.download_button("Export CSV", data=csv_data, file_name="shiptrack_export.csv", mime="text/csv", use_container_width=True)
            
    st.markdown("<hr style='border-color: var(--border-color);'>", unsafe_allow_html=True)
    
    # Fetch comprehensive analytics
    analytics_data = api.get_analytics()
    if not analytics_data:
        analytics_data = {}
    
    overview = analytics_data.get('overview', {'total': 0, 'delivered': 0, 'delivery_rate': 0.0, 'avg_time': 0})
    
    k1, k2, k3, k4 = st.columns(4)
    with k1: render_metric_card("Total Shipments", overview.get('total', 0), "📦")
    with k2: render_metric_card("Delivered", overview.get('delivered', 0), "✅")
    with k3: render_metric_card("Delivery Rate", f"{overview.get('delivery_rate', 0)}%", "📈")
    with k4: render_metric_card("Avg Delivery Time", f"{overview.get('avg_time', 0)}d", "⏱️")
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Row 1: Status Distribution + Shipments Over Time
    r1c1, r1c2 = st.columns(2)
    with r1c1:
        st.markdown("<h4>Status Distribution</h4>", unsafe_allow_html=True)
        by_status = analytics_data.get('by_status', [])
        if by_status:
            st.plotly_chart(status_distribution_chart(by_status), use_container_width=True)
        else:
            st.info("No status data available")
            
    with r1c2:
        st.markdown("<h4>Shipments Over Time</h4>", unsafe_allow_html=True)
        over_time = analytics_data.get('shipments_over_time', [])
        st.plotly_chart(shipments_over_time_chart(over_time), use_container_width=True)
        
    # Row 2: Delivery Time Distribution + Delivery by Carrier
    r2c1, r2c2 = st.columns(2)
    with r2c1:
        st.markdown("<h4>Delivery Time Distribution</h4>", unsafe_allow_html=True)
        dist = analytics_data.get('delivery_time_distribution', [])
        st.plotly_chart(delivery_time_distribution_chart(dist), use_container_width=True)
        
    with r2c2:
        st.markdown("<h4>Avg Delivery Time by Carrier</h4>", unsafe_allow_html=True)
        by_carrier = analytics_data.get('avg_delivery_by_carrier', [])
        st.plotly_chart(delivery_time_by_carrier_chart(by_carrier), use_container_width=True)
        
    # Row 3: Delivery by Location + Frequent Hubs
    r3c1, r3c2 = st.columns(2)
    with r3c1:
        st.markdown("<h4>Avg Delivery Time by Location</h4>", unsafe_allow_html=True)
        by_location = analytics_data.get('avg_delivery_by_location', [])
        st.plotly_chart(delivery_time_by_location_chart(by_location), use_container_width=True)
        
    with r3c2:
        st.markdown("<h4>Most Frequent Hubs</h4>", unsafe_allow_html=True)
        common = analytics_data.get('common_locations', [])
        st.plotly_chart(location_frequency_chart(common), use_container_width=True)
        
    # Row 4: Stale Shipments + Recent Activity
    st.markdown("<hr style='border-color: var(--border-color);'>", unsafe_allow_html=True)
    r4c1, r4c2 = st.columns(2)
    with r4c1:
        st.markdown("<h4>⚠️ Stale Shipments (No update > 7 days)</h4>", unsafe_allow_html=True)
        stale = analytics_data.get('stale_shipments', [])
        if stale:
            for s in stale[:5]:
                tracking = s.get('tracking_number', 'Unknown')
                status = s.get('status', 'Unknown')
                last_updated = s.get('last_updated', 'Unknown')
                st.markdown(f"- **{tracking}** — {status} — Last updated: {last_updated}")
        else:
            st.success("No stale shipments")
            
    with r4c2:
        st.markdown("<h4>Recent Tracking Activity</h4>", unsafe_allow_html=True)
        activity = analytics_data.get('recent_activity', [])
        st.plotly_chart(recent_activity_chart(activity), use_container_width=True)