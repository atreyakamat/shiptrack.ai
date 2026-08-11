# ShipTrack AI — API Contract

## Standard Response Envelopes

Every JSON API endpoint must return one of these two standard envelopes.

### Success Response (2xx)
```json
{
    "success": true,
    "data": { ... } // or [...]
}
```

### Error Response (4xx, 5xx)
```json
{
    "success": false,
    "error": {
        "code": "ERROR_CODE",
        "message": "User-facing error message."
    }
}
```

## Canonical Resource Schemas

### 1. Shipment
```json
{
    "id": 1,
    "tracking_number": "EM740043207IN",
    "carrier": "india_post",
    "description": "Important documents", // Or null
    "category": "documents",
    "status": "IN_TRANSIT",
    "current_location": "Bicholim S.O", // Or null
    "origin": "Goa", // Or null
    "destination": "Mumbai", // Or null
    "booked_at": "2026-08-11T09:32:00", // ISO 8601 or null
    "last_updated": "2026-08-11T14:00:00", // ISO 8601 or null
    "expected_delivery": "2026-08-15T00:00:00", // ISO 8601 or null
    "priority": "normal",
    "notes": null,
    "is_archived": false,
    "article_type": "Parcel", // Or null
    "tariff": "50.00", // Or null
    "origin_pincode": "403504", // Or null
    "destination_pincode": "400001", // Or null
    "last_successful_sync": "2026-08-11T14:00:00", // ISO 8601 or null
    "last_attempted_sync": "2026-08-11T14:00:00", // ISO 8601 or null
    "last_failed_sync": null, // ISO 8601 or null
    "last_error": null,
    "created_at": "2026-08-10T10:00:00", // ISO 8601
    "updated_at": "2026-08-11T14:00:00"  // ISO 8601
}
```

### 2. Tracking Event
```json
{
    "id": 100,
    "shipment_id": 1,
    "status": "Item Dispatched",
    "location": "Panaji H.O.", // Or null
    "location_code": null,
    "latitude": 15.4909, // Or null
    "longitude": 73.8278, // Or null
    "description": "Bag dispatched to next facility", // Or null
    "raw_status": "Item Dispatched", // Or null
    "source": "india_post", // Or null
    "event_timestamp": "2026-08-11T09:32:00", // ISO 8601 string. Never send separated date/time strings to frontend.
    "created_at": "2026-08-11T10:00:00" // ISO 8601
}
```

## API Endpoints

### Auth
- **POST** `/api/auth/login` - Requires `{"email": "..."}`. Returns `{"token": "..."}` in data.
- **POST** `/api/auth/register` - Requires `{"email": "..."}`. Returns `{"token": "..."}` in data.

### Shipments
- **GET** `/api/shipments` - Lists all user shipments. Query Params: `search`, `status`, `carrier`.
- **POST** `/api/shipments` - Creates a new shipment.
- **GET** `/api/shipments/<id>` - Gets detail. Response `data` includes an `events` array.
- **PUT** `/api/shipments/<id>` - Updates metadata (notes, description, priority, category).
- **DELETE** `/api/shipments/<id>` - Hard deletes shipment.
- **POST** `/api/shipments/<id>/archive` - Marks as archived.

### Tracking
- **POST** `/api/shipments/<id>/refresh` - Pulls latest data from Carrier. Returns tracking summary.
- **POST** `/api/shipments/refresh-all` - Enqueues background refresh for all active shipments. Returns 202 Accepted.
- **GET** `/api/shipments/<id>/history` - Returns array of `TrackingEvent` objects.

### AI
- **GET** `/api/ai/<id>/summary` - Returns latest AI summary for shipment.
- **POST** `/api/ai/<id>/generate` - Forces regeneration of summary.
- **GET** `/api/ai/insights` - Global insights across all active shipments.
- **POST** `/api/ai/insights/generate` - Forces regeneration of global insights.

### Analytics
- **GET** `/api/analytics` - Main dashboard metrics.
- **GET** `/api/analytics/overview` - Charting data.
- **GET** `/api/analytics/export` - Returns raw CSV bytes (Special case, does not use envelope).

### OCR
- **POST** `/api/ocr` - Multipart file upload. Returns extracted text/confidence.
- **POST** `/api/ocr/confirm` - Confirms extraction and creates shipment.

### Health
- **GET** `/api/health` - Basic uptime check.
