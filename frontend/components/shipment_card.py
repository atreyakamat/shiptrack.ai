import streamlit as st
from components.status_badge import render_status_badge

def render_shipment_row(shipment):
    tracking_no = shipment.get('tracking_number') or 'UNKNOWN'
    desc = shipment.get('description') or 'No description'
    status = shipment.get('status') or 'UNKNOWN'
    carrier = shipment.get('carrier') or 'Unknown Carrier'
    is_archived = shipment.get('is_archived') or False
    
    if str(desc).strip().lower() in ("none", ""):
        desc = "No description"
        
    # Calculate days in transit if possible
    booked_at = shipment.get('booked_at')
    days_in_transit_html = ""
    if booked_at and status not in ['DELIVERED']:
        from datetime import datetime
        try:
            b_date = datetime.strptime(str(booked_at).split('T')[0], "%Y-%m-%d")
            days = (datetime.now() - b_date).days
            if days >= 0:
                days_in_transit_html = f'<div style="color: var(--accent-color); font-weight: 600; font-size: 0.8rem;">{days} days in transit</div>'
        except Exception:
            pass
            
    badge_html = render_status_badge(status)
    archived_style = "opacity: 0.6; filter: grayscale(100%);" if is_archived else ""
    
    html = (
        f'<div class="shipment-card" style="{archived_style}">'
        f'<div class="shipment-header">'
        f'<div>'
        f'<div class="shipment-tracking">{tracking_no}</div>'
        f'<div style="font-size: 0.8rem; color: var(--text-muted); margin-top: 2px;">{carrier} • {desc}</div>'
        f'</div>'
        f'<div style="text-align: right;">'
        f'{badge_html}'
        f'{days_in_transit_html}'
        f'</div>'
        f'</div>'
        f'</div>'
    )
    
    st.markdown(html, unsafe_allow_html=True)
