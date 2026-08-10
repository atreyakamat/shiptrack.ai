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
        normalized_counts[status] = normalized_counts.get(status, 0) + 1
        
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
    # Dummy implementation for area chart
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
        y=[10, 15, 13, 17, 21, 19],
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

def delivery_time_chart(data):
    fig = go.Figure(go.Bar(
        x=['Delhi', 'Mumbai', 'Bangalore', 'Chennai'],
        y=[2.5, 3.1, 4.0, 3.5],
        marker_color='#10B981'
    ))
    fig.update_layout(
        title="Avg Delivery Time (Days)",
        xaxis=dict(showgrid=False),
        yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.05)'),
        **chart_layout_updates
    )
    return fig

def location_frequency_chart(data):
    fig = go.Figure(go.Bar(
        x=[45, 30, 25, 15, 10],
        y=['Mumbai Hub', 'Delhi Sorting', 'Bangalore GPO', 'Chennai Hub', 'Kolkata'],
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
