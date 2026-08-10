import streamlit as st

def show(api):
    c1, c2 = st.columns([4, 1])
    with c1:
        st.markdown("<h2>Notifications</h2>", unsafe_allow_html=True)
    with c2:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Mark All Read", use_container_width=True):
            # API call to mark all read
            st.rerun()
            
    filter_val = st.radio("Filter", ["All", "Unread", "Read"], horizontal=True)
    
    notifs = api.get_notifications()
    if not notifs:
        st.info("No notifications to display.")
        return
        
    for n in notifs:
        if filter_val == "Unread" and n.get('read'): continue
        if filter_val == "Read" and not n.get('read'): continue
        
        icon = "🟢" if not n.get('read') else "⚪"
        bg = "rgba(56,189,248,0.05)" if not n.get('read') else "transparent"
        
        st.markdown(f"""
        <div style="background: {bg}; padding: 1rem; border: 1px solid var(--border-color); border-radius: 8px; margin-bottom: 0.5rem; display: flex; gap: 1rem; align-items: start;">
            <div style="font-size: 1.5rem;">{icon}</div>
            <div style="flex: 1;">
                <div style="font-weight: 500;">{n.get('message', 'New Notification')}</div>
                <div class="text-muted" style="font-size: 0.8rem; margin-top: 0.25rem;">
                    {n.get('timestamp', 'Just now')} • <a href="#" style="color: var(--accent-color);">View Shipment</a>
                </div>
            </div>
            <div>
        """, unsafe_allow_html=True)
        
        if not n.get('read'):
            if st.button("Mark Read", key=f"nr_{n.get('id')}"):
                api.mark_notification_read(n.get('id'))
                st.rerun()
                
        st.markdown("</div></div>", unsafe_allow_html=True)
