import streamlit as st

def show(api):
    st.markdown("<h2>🧠 AI Insights</h2>", unsafe_allow_html=True)
    
    st.caption("🤖 *AI-Generated Insights: This is an interpretation of structured tracking data, not official carrier statements.*")
    
    health = st.session_state.get('api_health', {})
    if health.get('demo_mode', False):
        st.warning("Running in Demo Mode - AI Insights may be simulated.")
        
    if st.button("✨ Generate Fresh Insights", type="primary"):
        with st.spinner("Analyzing shipping patterns..."):
            api.generate_insights()
            st.rerun()
            
    insights = api.get_insights()
    if not insights:
        st.info("No insights generated yet. Click the button above to analyze your shipments.")
        return
        
    st.markdown("""
        <div class="shipment-card" style="margin-bottom: 2rem;">
            <h3 style="margin-top: 0; color: var(--accent-color);">Executive Summary</h3>
            <p>Your delivery performance is <strong>optimal</strong>. 85% of packages are arriving on or before the expected delivery date.</p>
        </div>
    """, unsafe_allow_html=True)
    
    c1, c2 = st.columns(2)
    
    with c1:
        st.markdown("### Delivery Trends")
        st.info("📦 **Volume Spike:** You have a 20% increase in document shipments this month.")
        st.success("✅ **Carrier Performance:** Delhivery is currently 15% faster than India Post for your routes.")
        
    with c2:
        st.markdown("### Potential Delays")
        st.warning("⚠️ **Weather Alert:** Heavy rains in Mumbai may delay 3 active shipments.")
        st.error("🚨 **Stuck Package:** EY123456789IN has been at Delhi Sorting Hub for 48 hours.")
        
    st.markdown("<hr style='border-color: var(--border-color);'>", unsafe_allow_html=True)
    st.markdown("### Recent AI Summaries")
    
    # Dummy list of recent AI summaries for effect
    for i in range(1, 4):
        st.markdown(f"""
        <div style="padding: 1rem; border-left: 3px solid var(--accent-color); background: rgba(15,23,42,0.5); margin-bottom: 1rem;">
            <strong>Shipment #{i}000{i}</strong><br>
            <span class="text-muted">Package cleared customs ahead of schedule. Expected delivery revised to tomorrow.</span>
        </div>
        """, unsafe_allow_html=True)
