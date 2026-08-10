import streamlit as st
from components.shipment_card import render_shipment_row

def show(api):
    st.markdown("<h2>All Shipments</h2>", unsafe_allow_html=True)
    
    # Search and Filters
    c1, c2, c3, c4, c5 = st.columns([2, 1, 1, 1, 1])
    with c1:
        search = st.text_input("Search Tracking Number", placeholder="e.g. EY123456789IN")
    with c2:
        status_filter = st.selectbox("Status", ["All", "Booked", "In Transit", "Out for Delivery", "Delivered", "Delayed"])
    with c3:
        carrier_filter = st.selectbox("Carrier", ["All", "India Post", "Delhivery", "BlueDart"])
    with c4:
        cat_filter = st.selectbox("Category", ["All", "General", "Documents", "Package", "Government", "Legal"])
    with c5:
        sort_by = st.selectbox("Sort By", ["Newest", "Oldest", "Last Updated", "Status"])
        
    st.markdown("<hr style='border-color: var(--border-color); margin: 1rem 0;'>", unsafe_allow_html=True)
    
    # API call
    params = {}
    if search: params['search'] = search
    if status_filter != "All": params['status'] = status_filter
    if carrier_filter != "All": params['carrier'] = carrier_filter
    if cat_filter != "All": params['category'] = cat_filter
    
    shipments = api.get_shipments(**params)
    
    if not shipments:
        st.info("No shipments found matching criteria.")
        return
        
    for s in shipments:
        c_card, c_act = st.columns([5, 1])
        with c_card:
            render_shipment_row(s)
        with c_act:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("View", key=f"v_{s.get('id')}", use_container_width=True):
                st.session_state['current_shipment_id'] = s.get('id')
                st.session_state['current_page'] = 'shipment_detail'
                st.rerun()
            if st.button("Delete", key=f"d_{s.get('id')}", use_container_width=True, type="secondary"):
                if api.delete_shipment(s.get('id')):
                    st.success("Deleted")
                    st.rerun()
