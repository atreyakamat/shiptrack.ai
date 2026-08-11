import folium
import streamlit as st
from streamlit_folium import st_folium

def render_journey_map(events):
    \"\"\"
    Renders a Folium map showing the sequence of known tracking event coordinates.
    \"\"\"
    # Extract valid coordinates from events (assuming they are sorted earliest to latest or we reverse them)
    # Actually, tracking history is usually newest first. We need oldest first for the journey path.
    valid_points = []
    
    # events is expected to be newest first, so reverse to get chronological path
    for event in reversed(events):
        lat = event.get('latitude')
        lng = event.get('longitude')
        loc = event.get('location', 'Unknown')
        status = event.get('status', 'Unknown')
        
        if lat is not None and lng is not None:
            # Avoid consecutive duplicate points
            if not valid_points or (valid_points[-1]['lat'] != lat or valid_points[-1]['lng'] != lng):
                valid_points.append({
                    'lat': lat,
                    'lng': lng,
                    'loc': loc,
                    'status': status
                })
                
    if not valid_points:
        st.info("No location coordinates available for this shipment journey.")
        return

    # Center map on the latest known location
    latest_point = valid_points[-1]
    m = folium.Map(location=[latest_point['lat'], latest_point['lng']], zoom_start=6, tiles="CartoDB positron")
    
    # Draw path
    coords = [[p['lat'], p['lng']] for p in valid_points]
    if len(coords) > 1:
        folium.PolyLine(coords, color="#4F46E5", weight=3, opacity=0.8).add_to(m)
        
    # Add markers
    for i, point in enumerate(valid_points):
        is_latest = (i == len(valid_points) - 1)
        color = 'green' if is_latest else 'blue'
        icon = 'info-sign'
        
        folium.Marker(
            [point['lat'], point['lng']],
            popup=f"<b>{point['loc']}</b><br>{point['status']}",
            tooltip=point['loc'],
            icon=folium.Icon(color=color, icon=icon)
        ).add_to(m)
        
    st_folium(m, width=700, height=400, returned_objects=[])
