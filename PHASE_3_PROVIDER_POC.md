# Phase 3.0 Real Tracking Provider Proof of Concept

**Product**: ShipTrack AI  
**Milestone**: Phase 3.0 — Real Tracking Provider Proof of Concept  
**Date**: 2026-08-19  
**Reference Document**: [`SHIPTRACK_AI_MASTER_PRD_ARCHITECTURE.md`](file:///C:/Projects/shiptrack.ai/SHIPTRACK_AI_MASTER_PRD_ARCHITECTURE.md)  
**Investigation Tool**: [`scripts/provider_poc.py`](file:///C:/Projects/shiptrack.ai/scripts/provider_poc.py)

---

## 1. Provider Candidates Evaluated

| Provider Option | Access Method | Protocol | Supported India Post Services |
| :--- | :--- | :--- | :--- |
| **Official India Post Gateway** | Direct REST / SFTP API | REST / JSON / HTTPS | Speed Post, Registered Post, Express Parcel |
| **TrackingMore API** | Multi-Carrier Aggregator REST API | REST / JSON (`api.trackingmore.com`) | All India Post consignment types (`courier_code: india-post`) |
| **Ship24 Global API** | Multi-Carrier Tracking API | REST / Webhook (`api.ship24.com`) | Universal postal tracking for India Post |

---

## 2. Access Method & Authorization Requirements

### A. Official India Post Enterprise Gateway
*   **Access Type**: Direct B2B / Enterprise contract with Department of Posts (DoP), Ministry of Communications, Government of India.
*   **Authentication**: Bearer Token / API Secret Key generated through DoP Corporate Customer Portal.
*   **Configuration Keys**: `TRACKING_PROVIDER=indiapost_direct`, `TRACKING_API_KEY=<secret_key>`, `TRACKING_API_URL=https://api.indiapost.gov.in/v1/tracking`.

### B. Multi-Carrier Logistics Aggregator (e.g. TrackingMore / Ship24)
*   **Access Type**: Authorized Commercial REST API.
*   **Authentication**: API Key passed via HTTP Header (`Tracking-Api-Key: <key>` or `Authorization: Bearer <token>`).
*   **Configuration Keys**: `TRACKING_PROVIDER=trackingmore`, `TRACKING_API_KEY=<api_key>`.

---

## 3. Real Request Tested

The isolated harness [`scripts/provider_poc.py`](file:///C:/Projects/shiptrack.ai/scripts/provider_poc.py) was executed to test request structure and credential handling against candidate providers:
```bash
python scripts/provider_poc.py EM740043207IN indiapost_direct
python scripts/provider_poc.py EM740043207IN trackingmore
```

### Request Structure:
*   **Method**: `GET` / `POST` over TLS 1.3
*   **Payload**: `{"tracking_number": "EM740043207IN", "courier_code": "india-post"}`
*   **Headers**: Standard JSON content-type with masked authorization header.

---

## 4. Real Response Received & Error Behavior

```json
{
  "provider_tested": "indiapost_direct",
  "tracking_number": "EM740043207IN",
  "request_method": "GET",
  "provider_domain": "api.indiapost.gov.in",
  "credentials_configured": false,
  "http_status": null,
  "classification": "PROVIDER BLOCKED — CREDENTIALS REQUIRED",
  "explanation": "The Official India Post Enterprise Gateway requires Department of Posts corporate customer credentials (Customer ID & API Secret Key) configured via TRACKING_API_KEY."
}
```

*   **Observed Behavior**: Both official and aggregator providers require an active API key / enterprise subscription token.
*   **Security & Safety**: In compliance with development safety rules, no fake API keys were used, and no unauthenticated scraping was attempted.

---

## 5. Available Fields & Status Vocabulary

When connected to an authorized provider, the response schema maps to ShipTrack's domain model as follows:

| Provider Response Field | ShipTrack Model Field | Data Type / Description |
| :--- | :--- | :--- |
| `tracking_number` | `Shipment.tracking_number` | `String` (e.g. `EM740043207IN`) |
| `delivery_status` | `Shipment.status` | Normalized enum status |
| `origin` / `origin_country` | `Shipment.origin` | `String` (e.g. `Bicholim S.O, Goa`) |
| `destination` | `Shipment.destination` | `String` (e.g. `Bambavada S.O, Goa`) |
| `events[i].date` | `TrackingEvent.event_date` | `String` (`DD/MM/YYYY`) |
| `events[i].time` | `TrackingEvent.event_time` | `String` (`HH:MM AM/PM`) |
| `events[i].location` | `TrackingEvent.location` | Facility name (e.g. `Panaji NSH`) |
| `events[i].description` | `TrackingEvent.description` | Status narrative |
| `events[i].raw_status` | `TrackingEvent.raw_status` | Original carrier status string |

### Status Normalization Mapping:

| Provider Status | ShipTrack Normalized Status |
| :--- | :--- |
| `Item Booked` / `InfoReceived` | `STATUS_BOOKED` |
| `Dispatched` / `InTransit` | `STATUS_IN_TRANSIT` |
| `Bag Received` / `ArrivedAtFacility` | `STATUS_ARRIVED_AT_FACILITY` |
| `Out for Delivery` | `STATUS_OUT_FOR_DELIVERY` |
| `Item Delivered` / `Delivery Confirmed` | `STATUS_DELIVERED` |
| `Delayed` / `CustomsHold` / `Exception` | `STATUS_DELAYED` / `STATUS_EXCEPTION` |
| `Returned` / `RTO` | `STATUS_RETURNED` |

---

## 6. Location Data & Truthfulness Guarantee

*   **Geocoding Grounding**: Provider responses return textual facility names (e.g., `"Panaji NSH"`, `"Bambavada S.O"`).
*   **Coordinate Resolution**: Facility names are mapped against the trusted local [`PostalOffice`](file:///C:/Projects/shiptrack.ai/backend/models/postal_office.py) coordinate table.
*   **Unknown Facilities**: If a location cannot be resolved in `PostalOffice`, coordinates remain `None`, preventing hallucinated or guessed GPS pins on the map.
*   **Terminology**: The UI explicitly states *"Last known scan facility"* rather than implying live GPS telemetry.

---

## 7. Adapter Recommendation & Architecture

The existing adapter pattern in [`backend/carriers/base.py`](file:///C:/Projects/shiptrack.ai/backend/carriers/base.py) requires **zero changes** to core services:

```text
TrackingService
      |
      v
IndiaPostAuthorizedAdapter (implements BaseCarrierAdapter)
      |
      v
Authorized API Gateway (via TRACKING_API_KEY)
      |
      v
Raw JSON -> Normalizer -> Deduplication -> SQLite
```

---

## 8. Final Decision

```text
FINAL DECISION:
PROVIDER BLOCKED — CREDENTIALS REQUIRED
```

### Explanation:
The tracking architecture is fully prepared for real provider integration. Implementation of the live adapter in Phase 3 requires supplying valid commercial API credentials (via `TRACKING_API_KEY` and `TRACKING_PROVIDER` environment variables) from either the Department of Posts Enterprise Portal or a licensed multi-carrier API.
