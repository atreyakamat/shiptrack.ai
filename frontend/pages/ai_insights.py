import streamlit as st
from components.metric_card import render_metric_card

def show(api):
    st.markdown("<h2>🧠 AI Insights & Health Overview</h2>", unsafe_allow_html=True)
    
    st.caption("🤖 *AI-Generated Insights: This is a rule-based interpretation of structured postal facility scans, not live telemetry or official carrier claims.*")
    
    if st.button("✨ Refresh AI Insights", type="primary"):
        with st.spinner("Analyzing shipping patterns..."):
            api.generate_insights()
            st.rerun()
            
    insights = api.get_insights()
    if not insights:
        st.info("No shipments found to analyze. Add a shipment to generate AI transit intelligence.")
        return
        
    summary_text = insights.get('summary', 'No summary available.')
    
    st.markdown(f"""
        <div style="padding: 1.25rem; border-radius: 8px; border: 1px solid var(--border-color); background: rgba(56,189,248,0.05); margin-bottom: 2rem;">
            <h3 style="margin-top: 0; color: var(--accent-color);">Executive Summary</h3>
            <p style="font-size: 1.05rem; margin-bottom: 0;">{summary_text}</p>
        </div>
    """, unsafe_allow_html=True)
    
    m1, m2, m3, m4 = st.columns(4)
    with m1: render_metric_card("Total Tracked", insights.get('total_count', 0), "📦")
    with m2: render_metric_card("Normal Transit", insights.get('normal_count', 0), "🚚", "var(--status-transit)")
    with m3: render_metric_card("Slow Movement", insights.get('watch_count', 0), "⏱️", "var(--status-out)")
    with m4: render_metric_card("Delayed / Needing Attention", insights.get('delayed_count', 0), "⚠️", "var(--status-delayed)")
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    c1, c2 = st.columns(2)
    
    with c1:
        st.markdown("### 📋 AI Recommendations")
        recs = insights.get('recommendations', [])
        if recs:
            for r in recs:
                st.info(f"💡 {r}")
        else:
            st.success("✅ All tracked shipments are moving normally with no actionable warnings.")
            
    with c2:
        st.markdown("### ⚠️ Delayed Shipments")
        delayed_list = insights.get('delayed_shipments', [])
        if delayed_list:
            for d in delayed_list:
                st.warning(f"**{d.get('tracking_number')}** — Status: *{d.get('status')}* — Last seen at: **{d.get('current_location')}**")
        else:
            st.success("✅ No delayed shipments or carrier exceptions detected.")
