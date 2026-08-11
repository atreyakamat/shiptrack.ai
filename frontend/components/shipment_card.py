import streamlit as st
from components.status_badge import render_status_badge

import textwrap

def render_shipment_row(shipment):
    tracking_no = shipment.get('tracking_number') or 'UNKNOWN'
    desc = shipment.get('description') or 'No description'
    status = shipment.get('status') or 'UNKNOWN'
    location = shipment.get('current_location') or 'Location unavailable'
    carrier = shipment.get('carrier') or 'Unknown Carrier'
    updated = shipment.get('last_updated') or 'Unknown'
    origin = shipment.get('origin') or 'Origin unavailable'
    destination = shipment.get('destination') or 'Destination unavailable'
    is_archived = shipment.get('is_archived') or False
    
    if str(desc).strip().lower() == "none":
        desc = "No description"
    if str(location).strip().lower() == "none":
        location = "Location unavailable"
        
    # Calculate days in transit if possible
    booked_at = shipment.get('booked_at')
    days_in_transit_html = ""
    if booked_at and status not in ['DELIVERED']:
        from datetime import datetime
        try:
            b_date = datetime.strptime(booked_at.split('T')[0], "%Y-%m-%d")
            days = (datetime.now() - b_date).days
            if days >= 0:
                days_in_transit_html = f'<div style="color: var(--accent-color); font-weight: 600; font-size: 0.8rem;">{days} days in transit</div>'
        except Exception:
            pass
            
    badge_html = render_status_badge(status)
    archived_style = "opacity: 0.6; filter: grayscale(100%);" if is_archived else ""
    
    html = f"""
    <div class="shipment-card" style="{archived_style}">
        <div class="shipment-header">
            <div>
                <div class="shipment-tracking">{tracking_no}</div>
                <div style="font-size: 0.8rem; color: var(--text-muted); margin-top: 2px;">{carrier} • {desc}</div>
            </div>
            <div style="text-align: right;">
                {badge_html}
                {days_in_transit_html}
            </div>
        </div>
        <div class="shipment-body" style="margin-top: 1rem; padding: 0.75rem; background: rgba(0,0,0,0.2); border-radius: 8px;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
                <div style="font-size: 0.8rem;">
                    <div style="color: var(--text-muted); font-size: 0.7rem; text-transform: uppercase;">Origin</div>
                    <div style="font-weight: 500;">{origin}</div>
                </div>
                <div style="color: var(--text-muted); font-size: 1.2rem;">→</div>
                <div style="font-size: 0.8rem; text-align: right;">
                    <div style="color: var(--text-muted); font-size: 0.7rem; text-transform: uppercase;">Destination</div>
                    <div style="font-weight: 500;">{destination}</div>
                </div>
            </div>
            <div style="border-top: 1px dashed var(--border-color); padding-top: 0.5rem; margin-top: 0.5rem; display: flex; align-items: center; gap: 0.5rem;">
                <span style="color: var(--accent-color); font-size: 1rem;">📍</span>
                <span style="font-size: 0.85rem; color: var(--text-primary);">Currently at: <strong>{location}</strong></span>
            </div>
        </div>
        <div class="shipment-footer">
            <span style="color: var(--text-muted);">Last Updated: {updated}</span>
        </div>
    </div>
    """
    
    st.markdown(textwrap.dedent(html).strip(), unsafe_allow_html=True)
