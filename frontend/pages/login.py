import streamlit as st

def show(api):
    st.markdown("<h1 style='text-align: center;'>📦 ShipTrack AI</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center;'>Please authenticate to access the application.</p>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        tab1, tab2 = st.tabs(["Log In", "Register"])
        
        with tab1:
            with st.form("login_form"):
                email = st.text_input("Email")
                password = st.text_input("Password", type="password")
                submit = st.form_submit_button("Log In", use_container_width=True)
                
                if submit:
                    if not email or not password:
                        st.error("Please enter email and password.")
                    else:
                        token = api.login(email, password)
                        if token:
                            st.session_state.auth_token = token
                            st.rerun()

        with tab2:
            with st.form("register_form"):
                reg_email = st.text_input("Email")
                reg_password = st.text_input("Password", type="password")
                reg_submit = st.form_submit_button("Register", use_container_width=True)
                
                if reg_submit:
                    if not reg_email or not reg_password:
                        st.error("Please enter email and password.")
                    else:
                        token = api.register(reg_email, reg_password)
                        if token:
                            st.session_state.auth_token = token
                            st.success("Registration successful! Logging in...")
                            st.rerun()
