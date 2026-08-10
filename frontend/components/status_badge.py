def get_status_class(status):
    status_lower = str(status).lower()
    if status_lower in ['delivered']:
        return "status-delivered"
    elif status_lower in ['in transit', 'transit']:
        return "status-in-transit"
    elif status_lower in ['out for delivery', 'out']:
        return "status-out-for-delivery"
    elif status_lower in ['delayed', 'exception']:
        return "status-delayed"
    else:
        return "status-booked"

def render_status_badge(status):
    css_class = get_status_class(status)
    return f'<span class="status-badge {css_class}">{status}</span>'
