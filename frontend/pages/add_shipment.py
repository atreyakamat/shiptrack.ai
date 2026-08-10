import streamlit as st

def show(api):
    st.markdown("<h2>Add New Shipment</h2>", unsafe_allow_html=True)
    
    with st.form("add_shipment_form"):
        col1, col2 = st.columns(2)
        with col1:
            tracking_number = st.text_input("Tracking Number *", placeholder="e.g. EY123456789IN")
            carrier = st.selectbox("Carrier *", ["India Post", "Delhivery", "BlueDart", "DTDC"])
            category = st.selectbox("Category", ["General", "Documents", "Package", "Government", "Legal", "Personal", "Business"])
            
        with col2:
            description = st.text_input("Description", placeholder="What's in the package?")
            priority = st.selectbox("Priority", ["Normal", "Low", "High", "Urgent"])
            notes = st.text_area("Notes", placeholder="Any special instructions?")
            
        submit = st.form_submit_button("➕ Add Shipment", type="primary", use_container_width=True)
        
        if submit:
            if not tracking_number or not carrier:
                st.error("Tracking Number and Carrier are required.")
            else:
                data = {
                    "tracking_number": tracking_number,
                    "carrier": carrier,
                    "category": category,
                    "description": description,
                    "priority": priority,
                    "notes": notes
                }
                res = api.create_shipment(data)
                if res:
                    st.success(f"Shipment {tracking_number} added successfully!")
                    st.session_state['current_shipment_id'] = res.get('id', tracking_number)
                    st.session_state['current_page'] = 'shipment_detail'
                    st.rerun()
