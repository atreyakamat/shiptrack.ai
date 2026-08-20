import streamlit as st

def show(api):
    st.markdown("<h2>Scan Postal Receipt</h2>", unsafe_allow_html=True)
    st.markdown("<p class='text-muted'>Upload an image of your postal receipt to auto-extract the tracking number.</p>", unsafe_allow_html=True)
    
    uploaded_file = st.file_uploader("Upload Receipt Image", type=['png', 'jpg', 'jpeg', 'webp'])
    
    if uploaded_file is not None:
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.image(uploaded_file, caption="Uploaded Receipt", use_container_width=True)
            
        with col2:
            st.markdown("### Extraction Results")
            if st.button("Process Image", type="primary"):
                with st.spinner("Extracting text via AI OCR..."):
                    res = api.upload_ocr(uploaded_file)
                    
                    if res:
                        st.session_state['ocr_result'] = res
                        st.rerun()
                        
            if 'ocr_result' in st.session_state:
                res = st.session_state['ocr_result']
                
                # Check for Demo Mode flag in result
                is_demo = res.get('is_demo', False)
                if is_demo:
                    st.warning("⚠️ **DEMO OCR MODE** - The OCR engine (EasyOCR) is not installed. This is a simulated fallback result and NOT a real extraction from your image.")
                    st.info("To enable Real OCR, install the easyocr python package.")
                
                candidates = res.get('candidates', [])
                selected_tracking = None
                
                if candidates:
                    st.markdown("### Candidates Found")
                    options = []
                    for c in candidates:
                        num = c.get('tracking_number')
                        conf = c.get('confidence')
                        if conf is not None:
                            options.append(f"{num} ({conf*100:.0f}% confidence)")
                        else:
                            options.append(num)
                    
                    options.append("Enter manually...")
                    selection = st.selectbox("Select Extracted Tracking Number", options)
                    
                    if selection == "Enter manually...":
                        selected_tracking = st.text_input("Enter Tracking Number", value="")
                    else:
                        selected_tracking = selection.split(" ")[0]
                else:
                    st.warning("Could not automatically extract a valid India Post tracking number from this receipt.")
                    st.info("Ensure the image is clear, well-lit, and the tracking number (e.g. EM123456789IN) is visible.")
                    selected_tracking = st.text_input("Enter Tracking Number Manually", value="")
                        
                with st.expander("Show Full Extracted Text"):
                    st.text(res.get('ocr_text', res.get('full_text', 'No text extracted.')))
                    
                if selected_tracking:
                    if st.button("Confirm & Add Shipment", type="primary"):
                        doc_id = res.get('id')
                        if doc_id:
                            c_res = api.confirm_ocr({
                                "document_id": doc_id,
                                "tracking_number": selected_tracking,
                                "carrier": "india_post"
                            })
                        else:
                            s_data = {
                                "tracking_number": selected_tracking,
                                "carrier": "india_post",
                                "description": "Scanned from receipt"
                            }
                            c_res = api.create_shipment(s_data)
                            
                        if c_res:
                            if 'ocr_result' in st.session_state:
                                del st.session_state['ocr_result']
                            st.session_state['current_shipment_id'] = c_res.get('id')
                            st.session_state['current_page'] = 'shipment_detail'
                            st.rerun()
