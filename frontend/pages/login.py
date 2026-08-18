import streamlit as st

def show(api):
    st.markdown("<h1 style='text-align: center;'>📦 ShipTrack AI</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: var(--text-muted);'>Please authenticate to access the application.</p>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        tab1, tab2 = st.tabs(["Log In", "Register"])
        
        with tab1:
            with st.form("login_form"):
                email = st.text_input("Email", placeholder="admin@shiptrack.ai")
                password = st.text_input("Password", type="password", placeholder="Enter your password")
                submit = st.form_submit_button("Log In", use_container_width=True, type="primary")
                
                if submit:
                    if not email:
                        st.error("Please enter email.")
                    elif not password:
                        st.error("Please enter password.")
                    else:
                        token = api.login(email.strip(), password)
                        if token:
                            st.session_state.auth_token = token
                            st.rerun()

        with tab2:
            with st.form("register_form"):
                reg_email = st.text_input("Email", placeholder="user@shiptrack.ai")
                reg_password = st.text_input("Password", type="password", placeholder="Create a password")
                reg_confirm_password = st.text_input("Confirm Password", type="password", placeholder="Re-enter your password")
                reg_submit = st.form_submit_button("Register", use_container_width=True, type="primary")
                
                if reg_submit:
                    if not reg_email:
                        st.error("Please enter email.")
                    elif not reg_password:
                        st.error("Please enter password.")
                    elif len(reg_password) < 6:
                        st.error("Password must be at least 6 characters.")
                    elif reg_password != reg_confirm_password:
                        st.error("Passwords do not match.")
                    else:
                        token = api.register(reg_email.strip(), reg_password)
                        if token:
                            st.session_state.auth_token = token
                            st.success("Registration successful! Logging in...")
                            st.rerun()
