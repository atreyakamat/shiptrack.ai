import streamlit as st
from components.metric_card import render_metric_card
from components.charts import (
    status_distribution_chart, 
    shipments_over_time_chart,
    delivery_time_chart,
    location_frequency_chart
)

def show(api):
    st.markdown("<h2>Analytics</h2>", unsafe_allow_html=True)
    
    # Filters
    c1, c2, c3, c4 = st.columns([2, 2, 2, 1])
    with c1: st.selectbox("Date Range", ["Last 7 Days", "Last 30 Days", "This Year", "All Time"])
    with c2: st.selectbox("Carrier", ["All", "India Post", "Delhivery"])
    with c3: st.selectbox("Category", ["All", "General", "Documents"])
    with c4:
        st.markdown("<br>", unsafe_allow_html=True)
        csv_data = api.export_csv()
        if csv_data:
            st.download_button("Export CSV", data=csv_data, file_name="shiptrack_export.csv", mime="text/csv", use_container_width=True)
            
    st.markdown("<hr style='border-color: var(--border-color);'>", unsafe_allow_html=True)
    
    stats = api.get_analytics()
    if not stats:
        stats = {'total': 0, 'delivered': 0, 'delivery_rate': 0.0, 'avg_time': 0}
        
    k1, k2, k3, k4 = st.columns(4)
    with k1: render_metric_card("Total Shipments", stats.get('total', 0), "📦")
    with k2: render_metric_card("Delivered", stats.get('delivered', 0), "✅")
    with k3: render_metric_card("Delivery Rate", f"{stats.get('delivery_rate', 0)}%", "📈")
    with k4: render_metric_card("Avg Delivery Time", f"{stats.get('avg_time', 0)}d", "⏱️")
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    data = api.get_shipments() or []
    
    r1c1, r1c2 = st.columns(2)
    with r1c1:
        st.markdown("<h4>Status Distribution</h4>", unsafe_allow_html=True)
        st.plotly_chart(status_distribution_chart(data), use_container_width=True)
    with r1c2:
        st.markdown("<h4>Shipments Per Month</h4>", unsafe_allow_html=True)
        st.plotly_chart(shipments_over_time_chart(data), use_container_width=True)
        
    r2c1, r2c2 = st.columns(2)
    with r2c1:
        st.markdown("<h4>Avg Delivery Time by Location</h4>", unsafe_allow_html=True)
        st.plotly_chart(delivery_time_chart(data), use_container_width=True)
    with r2c2:
        st.markdown("<h4>Most Frequent Hubs</h4>", unsafe_allow_html=True)
        st.plotly_chart(location_frequency_chart(data), use_container_width=True)
