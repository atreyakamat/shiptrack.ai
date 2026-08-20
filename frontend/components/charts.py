import plotly.graph_objects as go
import plotly.express as px

# Shared theme config
dark_template = "plotly_dark"
chart_layout_updates = dict(
    paper_bgcolor='rgba(0,0,0,0)',
    plot_bgcolor='rgba(0,0,0,0)',
    font=dict(family="Inter, sans-serif", color="#F8FAFC"),
    margin=dict(l=20, r=20, t=40, b=20)
)

def status_distribution_chart(data):
    if not data:
        return go.Figure()
        
    colors = {
        'Delivered': '#10B981',
        'In Transit': '#38BDF8',
        'Out For Delivery': '#F59E0B',
        'Booked': '#94A3B8',
        'Delayed': '#EF4444',
        'Exception': '#EF4444',
        'Unknown': '#64748B'
    }
    
    # Capitalize for display
    normalized_counts = {}
    for s in data:
        status = s.get('status', 'Unknown').replace('_', ' ').title()
        normalized_counts[status] = normalized_counts.get(status, 0) + s.get('count', 1)
        
    labels = list(normalized_counts.keys())
    values = list(normalized_counts.values())
    
    marker_colors = [colors.get(l, '#38BDF8') for l in labels]

    fig = go.Figure(data=[go.Pie(
        labels=labels, 
        values=values, 
        hole=.6,
        marker=dict(colors=marker_colors, line=dict(color='#0F172A', width=2))
    )])
    fig.update_layout(
        title_text="Shipment Status",
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5),
        **chart_layout_updates
    )
    return fig

def shipments_over_time_chart(data):
    """Create area chart from shipments over time data."""
    if not data:
        fig = go.Figure()
        fig.add_annotation(text="No historical data available", xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False)
        fig.update_layout(**chart_layout_updates)
        return fig
    
    periods = [d.get('period', '') for d in data]
    counts = [d.get('count', 0) for d in data]
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=periods,
        y=counts,
        fill='tozeroy',
        mode='lines+markers',
        line=dict(color='#38BDF8', width=3),
        marker=dict(size=8, color='#0F172A', line=dict(width=2, color='#38BDF8'))
    ))
    fig.update_layout(
        title="Shipments Over Time",
        xaxis=dict(showgrid=False),
        yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.05)'),
        **chart_layout_updates
    )
    return fig

def delivery_time_distribution_chart(data):
    """Create histogram from delivery time distribution data."""
    if not data:
        fig = go.Figure()
        fig.add_annotation(text="No delivery data available", xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False)
        fig.update_layout(**chart_layout_updates)
        return fig
    
    ranges = [d.get('range', '') for d in data]
    counts = [d.get('count', 0) for d in data]
    
    fig = go.Figure(go.Bar(
        x=ranges,
        y=counts,
        marker_color='#10B981'
    ))
    fig.update_layout(
        title="Delivery Time Distribution",
        xaxis=dict(showgrid=False, tickangle=45),
        yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.05)'),
        **chart_layout_updates
    )
    return fig

def delivery_time_by_carrier_chart(data):
    """Create bar chart for average delivery time by carrier."""
    if not data:
        fig = go.Figure()
        fig.add_annotation(text="No carrier delivery data available", xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False)
        fig.update_layout(**chart_layout_updates)
        return fig
    
    carriers = [d.get('carrier', '') for d in data]
    avg_days = [d.get('avg_days', 0) for d in data]
    counts = [d.get('count', 0) for d in data]
    
    fig = go.Figure(go.Bar(
        x=carriers,
        y=avg_days,
        marker_color='#38BDF8',
        text=[f"{d} days ({c} shipments)" for d, c in zip(avg_days, counts)],
        textposition='auto'
    ))
    fig.update_layout(
        title="Avg Delivery Time by Carrier",
        xaxis=dict(showgrid=False),
        yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.05)', title="Days"),
        **chart_layout_updates
    )
    return fig

def delivery_time_by_location_chart(data):
    """Create horizontal bar chart for average delivery time by location."""
    if not data:
        fig = go.Figure()
        fig.add_annotation(text="No location delivery data available", xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False)
        fig.update_layout(**chart_layout_updates)
        return fig
    
    locations = [d.get('location', '') for d in data]
    avg_days = [d.get('avg_days', 0) for d in data]
    counts = [d.get('count', 0) for d in data]
    
    fig = go.Figure(go.Bar(
        x=avg_days,
        y=locations,
        orientation='h',
        marker_color='#F59E0B',
        text=[f"{d} days ({c} shipments)" for d, c in zip(avg_days, counts)],
        textposition='auto'
    ))
    fig.update_layout(
        title="Avg Delivery Time by Location",
        xaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.05)', title="Days"),
        yaxis=dict(showgrid=False, autorange="reversed"),
        **chart_layout_updates
    )
    return fig

def location_frequency_chart(data):
    if not data:
        fig = go.Figure()
        fig.add_annotation(text="No location data available", xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False)
        fig.update_layout(**chart_layout_updates)
        return fig
    
    locations = [d.get('location', '') for d in data]
    counts = [d.get('count', 0) for d in data]
    
    fig = go.Figure(go.Bar(
        x=counts,
        y=locations,
        orientation='h',
        marker_color='#38BDF8'
    ))
    fig.update_layout(
        title="Frequent Transit Locations",
        xaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.05)'),
        yaxis=dict(showgrid=False, autorange="reversed"),
        **chart_layout_updates
    )
    return fig

def recent_activity_chart(data):
    """Create a simple activity timeline from recent events."""
    if not data:
        fig = go.Figure()
        fig.add_annotation(text="No recent activity", xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False)
        fig.update_layout(**chart_layout_updates)
        return fig
    
    # Extract timestamps and statuses
    times = []
    statuses = []
    for e in data:
        ts = e.get('event_timestamp') or e.get('created_at')
        if ts:
            times.append(ts)
            statuses.append(e.get('status', 'Update'))
    
    if not times:
        fig = go.Figure()
        fig.add_annotation(text="No timestamped activity", xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False)
        fig.update_layout(**chart_layout_updates)
        return fig
    
    fig = go.Figure(go.Scatter(
        x=times,
        y=statuses,
        mode='markers+lines',
        marker=dict(size=10, color='#38BDF8'),
        line=dict(color='#38BDF8', width=2, dash='dot')
    ))
    fig.update_layout(
        title="Recent Tracking Activity",
        xaxis=dict(showgrid=False),
        yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.05)'),
        **chart_layout_updates
    )
    return fig