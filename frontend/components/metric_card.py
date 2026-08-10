import streamlit as st

def render_metric_card(label, value, icon, color="var(--accent-color)"):
    html = f"""
    <div class="metric-card">
        <div class="metric-header">
            <span>{label}</span>
            <span style="color: {color}; font-size: 1.25rem;">{icon}</span>
        </div>
        <div class="metric-value">{value}</div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)
