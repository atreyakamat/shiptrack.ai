from frontend.utils.event_normalizer import normalize_tracking_events, get_progress_index, STATUS_STAGES

# Test with mock data similar to what the API returns
events = [
    {
        'event_timestamp': '2026-08-11T09:07:44',
        'status': 'Out for Delivery',
        'location': 'Bambavada S.O.',
        'description': 'Item Out for Delivery'
    },
    {
        'event_timestamp': '2026-08-11T08:13:44',
        'status': 'Item Received',
        'location': 'Bambavada S.O.',
        'description': None
    },
    {
        'event_timestamp': '2026-08-11T08:06:44',
        'status': 'Bag Received',
        'location': 'Bambavada S.O.',
        'description': ''
    }
]

normalized = normalize_tracking_events(events)
for i, e in enumerate(normalized):
    print(f'Event {i}:')
    print(f'  status: {e["status"]}')
    print(f'  location: {e["location"]}')
    print(f'  description: "{e["description"]}"')
    print(f'  date_display: {e["date_display"]}')
    print(f'  time_display: {e["time_display"]}')
    print(f'  is_latest: {e["is_latest"]}')
    print()

# Test progress index
print('Progress index tests:')
for status in ['BOOKED', 'DISPATCHED', 'IN_TRANSIT', 'OUT_FOR_DELIVERY', 'DELIVERED', 'OUT_FOR_DELIVERY']:
    idx = get_progress_index(status)
    print(f'  {status} -> index {idx} -> {STATUS_STAGES[idx][0]}')