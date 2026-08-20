# ShipTrack AI — Product Requirements & Architecture Master Document

**Document Type:** Product Requirements Document (PRD) + System Architecture Specification  
**Product:** ShipTrack AI  
**Document Status:** Living Master Reference  
**Current Development Priority:** Local application functionality  
**Deployment Infrastructure:** Deferred until explicitly approved  
**Primary Scope:** Shipment management, tracking intelligence, receipt OCR, truthful location visualization, analytics, and rule-based AI insights

---

# 1. Product Definition

## 1.1 Product Summary

ShipTrack AI is a personal and small-business **shipment intelligence dashboard** designed to consolidate postal shipments into one searchable and visual workspace.

The product allows a user to:

- Add shipment tracking numbers manually.
- Maintain a history of previously added shipments.
- Retrieve and store tracking events through a carrier-provider architecture.
- View shipment status and tracking history.
- Identify the latest known scan/facility.
- Visualize known shipment journey locations on a map.
- Upload postal receipts and extract tracking numbers using local OCR.
- Review and confirm OCR results before creating shipments.
- Generate truthful, rule-based AI summaries from structured tracking data.
- View real shipment analytics.
- Receive optional in-app notifications.
- Manage shipments through a dashboard.

The product must prioritize **truthful data representation** over artificial completeness.

It must never claim live GPS tracking when only postal scan/facility data is available.

---

# 2. Product Vision

## 2.1 Vision

Turn messy postal receipts and fragmented tracking information into a clean, understandable shipment intelligence system.

## 2.2 Core Value Proposition

Instead of repeatedly checking postal tracking pages and manually interpreting scan histories, ShipTrack AI provides:

1. A persistent shipment library.
2. A unified shipment timeline.
3. Last-known facility/location intelligence.
4. Visual journey mapping.
5. Receipt-to-shipment OCR.
6. Analytics derived from actual shipment history.
7. AI-assisted explanations of what the tracking data means.

## 2.3 Product Positioning

ShipTrack AI is **not** intended to be a GPS logistics platform.

It is a:

> Self-hosted shipment intelligence and tracking dashboard.

The system works from structured carrier tracking events and postal facility information.

---

# 3. Product Principles

These principles govern all future development.

## 3.1 Truth Over Simulation

Never fabricate:

- Tracking events
- Locations
- Coordinates
- Delivery dates
- Carrier responses
- GPS positions
- Analytics

Mock data may exist for development/testing but must always be explicitly identifiable as demo data.

## 3.2 Provider Failure Must Not Become Fake Success

If a real carrier provider is unavailable:

- Return a controlled provider error.
- Preserve existing shipment data.
- Do not silently fall back to mock data.

## 3.3 AI Is Interpretive, Not Authoritative

AI may explain structured facts.

AI must not invent facts.

## 3.4 Existing Data Must Be Preserved

A failed refresh must never destroy previously stored tracking history.

## 3.5 Local Application First

Current development priorities are:

1. Application functionality.
2. Real OCR.
3. Real analytics.
4. Real-world workflow testing.
5. UI/UX refinement.
6. Legitimate tracking-provider integration.

Docker, VPS, Nginx, SSL, and deployment infrastructure are explicitly deferred until separately approved.

---

# 4. Target Users

## 4.1 Primary User

An individual managing multiple postal shipments.

Typical needs:

- Track personal parcels.
- Remember tracking numbers.
- Quickly see shipment status.
- Understand where a parcel was last scanned.
- Avoid repeatedly searching postal websites.
- Store and retrieve historical shipments.

## 4.2 Secondary User

A small business operator managing outgoing and incoming postal shipments.

Typical needs:

- Track multiple orders.
- Identify delayed/stale shipments.
- Maintain shipment history.
- Analyze delivery performance.
- Extract tracking numbers from postal receipts.

---

# 5. MVP / Core Feature Set

## 5.1 Authentication

The application must provide:

- User registration/login as currently implemented.
- Password verification.
- JWT authentication.
- Protected API routes.
- Multi-tenant data isolation.

Every shipment-related query must be scoped to the authenticated user.

---

# 6. Shipment Management

## 6.1 Add Shipment

The user can manually create a shipment.

Required:

- Tracking number
- Carrier

Optional:

- Category
- Description
- Priority
- Notes
- Origin
- Destination

Validation must occur before database insertion.

## 6.2 Duplicate Handling

The system must detect duplicate shipments.

Expected behavior:

```text
HTTP 409
DUPLICATE_SHIPMENT
```

No generic 500 error.

## 6.3 Shipment List

The user can:

- Search tracking numbers.
- Filter by carrier.
- Filter by status.
- Filter by category.
- Filter by priority.
- View archived/non-archived shipments.
- Open shipment details.
- Refresh a shipment.

## 6.4 Shipment Detail

Shipment detail must display:

- Tracking number
- Carrier
- Status
- Last known facility
- Latest scan
- Last successful sync
- Days in transit
- Origin
- Destination
- Expected delivery, if actually available
- Priority
- Notes

---

# 7. Tracking System

## 7.1 Architecture

Tracking uses an adapter pattern.

```text
TrackingService
      |
      +---- Carrier Adapter
              |
              +---- India Post Adapter
              |
              +---- Mock Adapter
              |
              +---- Future Authorized Providers
```

The service layer must not depend directly on a specific carrier implementation.

## 7.2 Tracking Provider States

The system must distinguish:

### REAL

A legitimate provider returns actual carrier data.

### DEMO

The mock adapter intentionally returns simulated data for development/testing.

### PROVIDER_UNAVAILABLE

No legitimate provider is configured or the provider cannot currently be contacted.

The application must never silently transition:

```text
REAL → MOCK
```

## 7.3 India Post

The India Post adapter must not bypass CAPTCHA or anti-bot systems.

If no authorized live integration is available:

```text
503 PROVIDER_UNAVAILABLE
```

The UI should explain that live tracking requires an authorized tracking integration.

No fake tracking events may be returned in production mode.

## 7.4 Tracking Refresh

Refresh flow:

```text
User requests refresh
        ↓
Authentication
        ↓
Shipment ownership validation
        ↓
TrackingService
        ↓
Carrier adapter
        ↓
Provider response
        ↓
Normalize events
        ↓
Deduplicate events
        ↓
Resolve postal facility
        ↓
Update shipment
        ↓
Persist refresh log
        ↓
Generate/update AI insight
```

If refresh fails:

- Preserve existing events.
- Preserve last known location.
- Preserve last successful status.
- Record failure.
- Return a meaningful error.

---

# 8. Tracking Event Model

Each tracking event should support:

- Event date
- Event time
- Raw status
- Normalized status
- Facility/location name
- Description
- Latitude
- Longitude
- Provider/source
- Creation timestamp

The original carrier information should not be unnecessarily discarded during normalization.

## 8.1 Event Deduplication

Duplicate events must be prevented using stable event characteristics such as:

- date
- time
- status
- facility

Provider-specific identifiers should be used when available.

---

# 9. Status Model

The application should normalize carrier statuses into a controlled internal vocabulary.

Examples:

```text
BOOKED
IN_TRANSIT
ARRIVED_AT_FACILITY
OUT_FOR_DELIVERY
DELIVERED
DELAYED
EXCEPTION
UNKNOWN
```

Carrier-specific raw text should remain available where useful.

The UI should present friendly labels while preserving raw carrier information.

---

# 10. Location & Map Intelligence

## 10.1 Location Philosophy

ShipTrack AI does not provide live parcel GPS unless the provider genuinely supplies GPS telemetry.

The preferred terminology is:

- Last Known Facility
- Latest Scan Location
- Known Scan Locations
- Tracking Journey

Avoid implying:

- Live GPS
- Current GPS position

when only facility scans are available.

## 10.2 PostalOffice Model

Postal facility lookup should support:

- Name
- Pincode
- City
- State
- Latitude
- Longitude
- Office type

## 10.3 Map Flow

```text
Tracking Event
      ↓
Facility Name
      ↓
PostalOffice lookup
      ↓
Coordinates if known
      ↓
Map
```

If a facility cannot be resolved:

- Do not guess coordinates.
- Store the event without coordinates.
- Continue rendering the timeline.

---

# 11. Receipt OCR

## 11.1 Objective

Allow the user to upload a postal receipt and automatically identify the tracking number.

## 11.2 Workflow

```text
Upload Receipt
      ↓
Image Validation
      ↓
OpenCV Preprocessing
      ↓
EasyOCR
      ↓
Extract Text
      ↓
Detect Candidates
      ↓
Validate Candidates
      ↓
Confidence
      ↓
User Confirmation
      ↓
Create Shipment
```

## 11.3 Image Processing

Use OpenCV for:

- Grayscale conversion
- Scaling
- Contrast enhancement
- Thresholding where appropriate
- Noise reduction where useful

Do not apply aggressive transformations that make text less readable.

## 11.4 OCR Engine

EasyOCR is the preferred local OCR engine.

The application must distinguish:

```text
REAL OCR
```

from:

```text
DEMO OCR
```

A mock OCR fallback is acceptable for tests/development but must never be presented as real extraction.

## 11.5 Tracking Number Detection

Primary expected pattern:

```text
[A-Z]{2}[0-9]{9}IN
```

OCR normalization may account for common character confusion, but corrections must be conservative.

Potential OCR confusions include:

```text
O → 0
I → 1
S → 5
```

Do not blindly replace characters when doing so could corrupt a valid value.

## 11.6 Multiple Candidates

If multiple candidates are detected:

```text
Candidate A — 96%
Candidate B — 72%
```

The user must select the candidate.

Do not automatically choose the first regex match.

## 11.7 Low Confidence

If confidence is insufficient:

- Show the candidate.
- Request manual verification.
- Allow manual correction.
- Do not automatically create a shipment.

---

# 12. AI Insights

## 12.1 Purpose

AI exists to explain shipment data, not generate shipment data.

## 12.2 Current Preferred Architecture

The core AI behavior should remain deterministic/rule-based.

An external LLM may be added later for wording enhancement, but the structured tracking data remains the source of truth.

## 12.3 Inputs

AI may use:

- Current status
- Latest tracking event
- Previous tracking events
- Last known facility
- Time since latest scan
- Shipment age
- Actual delivery status
- Actual expected delivery information where provided

## 12.4 Health Classification

Example rules:

```text
NORMAL
Updated within 24 hours.

WATCH
No update for more than 1 day.

DELAYED
No update for more than 3 days.
```

These thresholds should be configurable rather than hardcoded if the product later supports carrier-specific behavior.

## 12.5 AI Rules

AI must never invent:

- Locations
- Events
- GPS
- Delivery dates
- Carrier responses
- Predictions unsupported by data

Example:

Structured data:

```text
Status: OUT_FOR_DELIVERY
Facility: Bambavada S.O.
Time: 09:07
```

Acceptable:

> The latest scan shows that the parcel is out for delivery from Bambavada S.O.

Unacceptable:

> Your parcel will definitely arrive at 2 PM.

---

# 13. Analytics

Analytics must be generated from actual database data.

Static/dummy chart data is not acceptable in the final application.

## 13.1 Dashboard Metrics

Show:

- Total shipments
- In transit
- Out for delivery
- Delivered
- Delayed
- Exceptions
- Needs attention

## 13.2 Shipment Activity

Calculate shipments over time from actual shipment creation records.

## 13.3 Frequent Hubs

Calculate facility frequency from actual tracking events.

Example:

```text
Mumbai NSH        17 scans
Panaji H.O.        9 scans
Bambavada S.O.     7 scans
```

## 13.4 Delivery Time

For delivered shipments where sufficient timestamps exist:

```text
Delivery Time = Delivered Timestamp - Booked Timestamp
```

Provide:

- Average
- Minimum
- Maximum
- Distribution

If insufficient historical data exists:

> Not enough historical data.

Never display fabricated values.

## 13.5 Stale Shipments

Identify shipments that have not received a recent update.

Do not automatically call a shipment delayed unless tracking data supports that classification.

---

# 14. Dashboard

The dashboard should function as a shipment command center.

Recommended structure:

```text
SHIPTRACK AI

Total       In Transit      Out for Delivery      Delivered
12          4               2                     5

NEEDS ATTENTION
----------------
Shipment A — No update for 4 days
Shipment B — Delivery exception

RECENT ACTIVITY
----------------
09:07 — EM740043207IN
Out for Delivery
Bambavada S.O.

RECENT SHIPMENTS
----------------
...
```

The dashboard must use real database data.

---

# 15. Notifications

The active product architecture implements:

- **In-App Notifications**: Active for status changes, deliveries, delays, and sync errors.
- **Notification Preferences**: Configurable per event type in User Settings.

The following external channels are **DEFERRED / LEGACY**:

- WhatsApp (deferred, not part of active product)
- Email (deferred, not part of active product)

Do not spend development effort on external messaging integrations.

Useful in-app triggers include:

- Shipment added
- Status changed
- Out for delivery
- Delivered
- Delayed
- Refresh failed

Notifications should not spam the user with duplicate events.

---

# 16. Error Handling

The API must use meaningful HTTP semantics.

| Situation | HTTP | Error Code |
|---|---:|---|
| Invalid input | 422 | `VALIDATION_ERROR` |
| Authentication failure | 401 | `UNAUTHORIZED` |
| Forbidden operation | 403 | `FORBIDDEN` |
| Resource missing | 404 | `NOT_FOUND` |
| Duplicate shipment | 409 | `DUPLICATE_SHIPMENT` |
| Rate limited | 429 | `PROVIDER_RATE_LIMITED` |
| Provider unavailable | 503 | `PROVIDER_UNAVAILABLE` |
| Provider timeout | 503 | `PROVIDER_TIMEOUT` |
| Provider network failure | 503 | `PROVIDER_NETWORK_ERROR` |
| Unexpected application failure | 500 | `INTERNAL_ERROR` |

A carrier/network failure must not be represented as an application 500.

## 16.1 Error Response Format

```json
{
  "success": false,
  "error": {
    "code": "PROVIDER_UNAVAILABLE",
    "message": "Live tracking is currently unavailable."
  }
}
```

Never expose:

- stack traces
- secrets
- filesystem paths
- database exception details

---

# 17. Security Architecture

## 17.1 Authentication

Protected endpoints require:

```text
Authorization: Bearer <JWT>
```

## 17.2 Multi-Tenant Isolation

Every user-owned resource must be scoped by authenticated user ID.

This applies to:

- Shipments
- Tracking events
- OCR documents
- AI summaries
- Refresh logs
- Notifications
- Preferences

A user must never access another user's resources.

## 17.3 Rate Limiting

Rate limiting protects:

- Authentication
- Tracking refresh
- OCR
- Other expensive endpoints

## 17.4 Secrets

Never hardcode:

- Passwords
- JWT secrets
- API keys
- Provider credentials

---

# 18. Database Architecture

## 18.1 Core Models

```text
User
Shipment
TrackingEvent
PostalOffice
AISummary
RefreshLog
Notification
NotificationPreference
OCRDocument
```

## 18.2 Relationships

```text
User
 ├── Shipments
 │     └── TrackingEvents
 │
 ├── AISummaries
 ├── OCRDocuments
 ├── Notifications
 ├── NotificationPreferences
 └── RefreshLogs
```

## 18.3 Database Support

Local development:

```text
SQLite
```

Future production:

```text
PostgreSQL
```

The application code should remain database-agnostic through SQLAlchemy.

---

# 19. API Architecture

## 19.1 Core API Groups

```text
/auth
/shipments
/tracking
/ocr
/analytics
/ai
/notifications
/health
```

## 19.2 Representative Endpoints

```text
POST   /auth/login

GET    /shipments
POST   /shipments
GET    /shipments/<id>
DELETE /shipments/<id>

POST   /shipments/<id>/refresh
GET    /shipments/<id>/history

POST   /ocr
POST   /ocr/confirm

GET    /analytics

GET    /ai/<id>/summary
```

All routes must maintain consistent authentication and error semantics.

---

# 20. Service Architecture

```text
Frontend
   ↓
Flask REST API
   ↓
Service Layer
   ├── ShipmentService
   ├── TrackingService
   ├── OCRService
   ├── AIService
   ├── AnalyticsService
   └── NotificationService
   ↓
Models / Database
```

Services should contain business logic rather than embedding business rules directly inside route handlers.

---

# 21. Frontend Architecture

## 21.1 Technology

- Streamlit
- Custom CSS
- Plotly
- Folium / streamlit-folium

## 21.2 Main Pages

```text
Login
Dashboard
Shipments
Add Shipment
Shipment Detail
OCR Scanner
Analytics
Settings
```

## 21.3 Frontend Rules

Never render:

```text
None
null
undefined
```

Never render raw HTML source.

HTML intended for Streamlit rendering must be safely normalized before rendering.

Dates/times should use consistent human-readable formatting.

---

# 22. Scheduler

Background scheduling may be used for shipment refreshes.

However:

- It must not duplicate executions.
- It must respect provider availability.
- It must not overwrite valid data with failed refreshes.
- It must not generate duplicate notifications.

The scheduler remains secondary to reliable manual refresh.

---

# 23. Mock Provider Architecture

Mock tracking exists strictly for:

- Development
- Automated testing
- UI demonstrations
- Edge-case simulation

It must support realistic scenarios such as:

- Booked
- In transit
- Arrived
- Out for delivery
- Delivered
- Delayed/exception
- Empty response
- Provider error

The UI must clearly indicate demo mode where applicable.

---

# 24. Testing Requirements

The project should maintain a comprehensive regression suite.

Required areas:

## Authentication

- Valid login
- Invalid password
- Invalid token
- Expired/invalid authentication

## Multi-Tenant Security

- User A cannot read User B shipment.
- User A cannot update User B shipment.
- User A cannot delete User B shipment.
- User A cannot refresh User B shipment.

## Shipment

- Valid creation
- Invalid tracking number
- Duplicate shipment
- Missing required fields

## Tracking

- Provider success
- Provider unavailable
- Timeout
- Network error
- Rate limit
- Duplicate events
- Refresh failure preserving old data

## OCR

- Valid receipt
- Multiple candidates
- Low confidence
- Manual correction
- Invalid tracking candidate
- Real OCR vs demo OCR

## AI

- Correct status interpretation
- No fabricated locations
- No fabricated delivery dates
- Correct stale/delayed classification

## Analytics

- Empty dataset
- One shipment
- Multiple shipments
- Delivered shipment
- Missing timestamps
- Real historical aggregation

---

# 25. Acceptance Criteria

The local application is considered functionally complete when:

### Shipment Management

- [ ] User can log in.
- [ ] User can add a shipment.
- [ ] Duplicate shipments return 409.
- [ ] User can search/filter shipments.
- [ ] User can open shipment details.
- [ ] User can archive/delete according to the implemented policy.

### Tracking

- [ ] Tracking provider adapter works correctly.
- [ ] Demo mode is explicit.
- [ ] Real provider mode never fabricates data.
- [ ] Refresh errors do not corrupt existing data.
- [ ] Tracking events are deduplicated.
- [ ] Latest known facility is correctly derived.

### Timeline

- [ ] No None/null/undefined output.
- [ ] Date/time formatting is consistent.
- [ ] Location is correctly displayed.
- [ ] Raw carrier information is preserved where useful.

### Map

- [ ] Known facilities are mapped.
- [ ] Unknown facilities are not fabricated.
- [ ] Map does not imply GPS tracking.

### OCR

- [ ] Real OCR works locally.
- [ ] Receipt preprocessing works.
- [ ] Tracking number detection works.
- [ ] Multiple candidates are handled.
- [ ] Low-confidence results require verification.
- [ ] User can manually correct OCR.

### AI

- [ ] Insights derive only from actual data.
- [ ] No hallucinated locations/events.
- [ ] No unsupported delivery predictions.
- [ ] AI output is clearly interpretive.

### Analytics

- [ ] No dummy chart data remains.
- [ ] Charts query real database records.
- [ ] Empty-data states are handled.
- [ ] Delivery metrics use actual timestamps.
- [ ] Hub statistics use actual events.

### Security

- [ ] Authentication works.
- [ ] Password verification works.
- [ ] Multi-user isolation works.
- [ ] Rate limiting works.
- [ ] Secrets are not hardcoded.

### Reliability

- [ ] No unexplained 500 responses.
- [ ] Provider failures return 503.
- [ ] Validation failures return 422.
- [ ] Duplicate shipments return 409.
- [ ] Existing data survives refresh failures.

---

# 26. Current Known External Dependency

## India Post

The architecture is ready for a legitimate India Post tracking data source.

However, direct CAPTCHA-bypass scraping must not be implemented.

Until an authorized provider/API is available:

```text
India Post live tracking = External Dependency / Blocked
```

The application should continue to support:

```text
Mock provider = Development/testing
```

without pretending that mock data is live.

---

# 27. Deferred Scope

The following are intentionally deferred:

- Docker deployment
- Docker Compose runtime
- VPS deployment
- Nginx production configuration
- SSL
- Domain setup
- WhatsApp integration
- Email integration
- Advanced LLM dependency
- Full nationwide geospatial dataset
- GPS telemetry
- Multi-carrier commercial integrations

These should not distract from completing the local product.

---

# 28. Recommended Development Roadmap

## Phase 1 — Core Stabilization

**Status: COMPLETE**

Validated:
- Authentication & JWT security
- Multi-tenant data isolation
- Shipment CRUD operations
- Duplicate tracking number handling (409 Conflict)
- Tracking service adapter architecture
- Timeline event ordering and rendering
- Postal facility mapping & Map visualization
- Truthful AI summary grounding
- API error semantics & 503 normalization
- Provider failure data preservation
- Frontend responsive rendering
- Empty states across all pages
- Automated regression testing (85/85 tests passing)

## Phase 2 — Local Product Completion

**Status: COMPLETE — LOCAL PRODUCT ACCEPTANCE PASSED**

- **2.1 Real OCR Architecture**: OpenCV preprocessing + EasyOCR integration with candidate extraction and normalization.
- **2.2 OCR Verification UX**: Interactive selectbox with multiple candidates, confidence scores, manual override, and confirmation before shipment creation.
- **2.3 Real Analytics**: 100% database-driven SQL metrics (Status distribution, shipments over time, frequent hubs, delivery histograms, carrier metrics).
- **2.4 Tracking Reliability**: Provider failure returns 503 (`PROVIDER_UNAVAILABLE` / `PROVIDER_TIMEOUT`), existing tracking history preserved, no live-to-mock silent fallback.
- **2.5 Shipment Detail**: Dynamic transit-day calculations, last known facility, sync state, expected delivery handling, null-safe rendering.
- **2.6 Dashboard Intelligence**: Needs Attention cards, Recent Tracking Activity feed, Stale Shipments alerts, database-driven Plotly charts.
- **2.7 Local Acceptance**: 85/85 tests passing, `compileall` passing, security and E2E isolation validated.

## Phase 2.5 — Real-World Local Validation

**Status: CURRENT**

- **2.5.1 Real OCR Receipt Validation**: Test with 3–5 real India Post receipt photographs across varying lighting, perspectives/tilts, blur, and text layouts.
- **2.5.2 Real User Workflow Testing**: End-to-end user journey walkthrough (Register -> Login -> Dashboard -> Add Shipment -> Refresh -> Timeline -> Map -> AI Insights -> Analytics -> Upload Receipt -> Confirm -> Search/Filter -> Settings).
- **2.5.3 Data Integrity Testing**: Verify deduplication of events across repeated refreshes, data persistence during provider failures, and clean recovery.
- **2.5.4 UI/UX Final Polish**: Minor polish strictly discovered during real usage (spacing, terminology, loading feedback, empty states).

## Phase 3 — Authorized Tracking Integration

**Status: BLOCKED BY EXTERNAL DEPENDENCY**

- Secure authorized India Post tracking API / commercial data aggregator.
- Activate production adapter without modifying core application services.
- Hard constraint: Do not attempt scraping or CAPTCHA bypass.

## Phase 4 — Production Deployment

**Status: DEFERRED (Only after explicit user approval)**

- Docker & Docker Compose
- PostgreSQL production configuration
- VPS deployment & Nginx reverse proxy
- SSL certificates & domain management
- Production backups & system health monitoring

---

## Development Gate Policy

ShipTrack AI development must proceed sequentially through the following gates:

1. **Local application correctness** (Complete)
2. **Real-world local workflow validation** (Current Gate)
3. **Legitimate external provider integration** (Blocked by external dependency)
4. **Production deployment** (Deferred)

A later phase must not introduce complexity into an earlier incomplete phase.

In particular:
- Docker must not be worked on unless explicitly approved.
- VPS deployment must not be worked on unless explicitly approved.
- Nginx/SSL must not be worked on unless explicitly approved.
- WhatsApp/Email must remain deferred.
- New features must not be added merely to increase feature count.
- Existing functionality must be preserved unless a demonstrated defect requires modification.
- When a phase passes its acceptance criteria, freeze it before proceeding.

---

# 29. Architecture Decision Records

## ADR-001 — Adapter-Based Tracking

**Decision:** Use carrier adapters.

**Reason:** Allows legitimate providers to be integrated without rewriting TrackingService.

## ADR-002 — No CAPTCHA Bypass

**Decision:** Do not circumvent India Post anti-bot controls.

**Reason:** Reliability, compliance, and technical integrity.

## ADR-003 — No Fake Live Data

**Decision:** Mock provider must never masquerade as a real provider.

**Reason:** User trust.

## ADR-004 — Facility Coordinates Are Not GPS

**Decision:** Postal-office coordinates represent facilities, not parcel telemetry.

**Reason:** Accurate terminology.

## ADR-005 — Rule-Based AI as Source of Truth

**Decision:** AI interprets structured data rather than generating shipment facts.

**Reason:** Prevent hallucination.

## ADR-006 — Local SQLite First

**Decision:** SQLite remains the local development database.

**Reason:** Simple local development while preserving SQLAlchemy compatibility with PostgreSQL later.

## ADR-007 — No WhatsApp/Email Scope

**Decision:** Do not implement WhatsApp or email notifications in the current product scope.

**Reason:** They are not required for the current product objective.

## ADR-008 — Application First

**Decision:** Complete and validate actual local application functionality before deployment infrastructure.

**Reason:** Avoid infrastructure overhead around an incompletely validated product.

---

# 30. Definition of Done

ShipTrack AI is considered **LOCAL APPLICATION FUNCTIONALLY COMPLETE** when:

1. The complete shipment lifecycle works.
2. Real OCR works locally.
3. OCR verification is trustworthy.
4. Analytics are entirely data-driven.
5. Tracking errors have correct HTTP semantics.
6. Existing shipment data survives provider failures.
7. Timeline contains no invalid/null rendering.
8. Map uses only known facility coordinates.
9. AI never invents shipment facts.
10. Dashboard is entirely based on real data.
11. Authentication and tenant isolation pass.
12. Full automated tests pass.
13. Manual end-to-end testing passes.
14. India Post remains explicitly marked as an external provider dependency until legitimate access is available.

---

# 31. Master Product State

The intended product state is:

```text
                         SHIPTRACK AI
                              │
              ┌───────────────┼────────────────┐
              │               │                │
          SHIPMENTS          OCR           TRACKING
              │               │                │
              │               ↓                ↓
              │          Receipt → ID     Provider Adapter
              │                                │
              └──────────────┬─────────────────┘
                             ↓
                      TRACKING DATABASE
                             │
             ┌───────────────┼────────────────┐
             ↓               ↓                ↓
          TIMELINE          MAP          ANALYTICS
             │               │                │
             └───────────────┼────────────────┘
                             ↓
                        AI INSIGHTS
                             │
                             ↓
                        DASHBOARD
```

The core product principle is:

> **Collect real data → preserve it → normalize it → visualize it → explain it.**

Never reverse that order by generating a visualization first and inventing data to fill it.

---

# 32. Master Reference Rule

This document is the primary product and architecture reference for future ShipTrack AI development.

When implementing a new feature:

1. Check this document first.
2. Preserve existing architecture unless there is a demonstrated reason to change it.
3. Prefer real data over placeholders.
4. Prefer explicit unavailable states over fabricated results.
5. Keep external provider dependencies isolated behind adapters.
6. Keep AI grounded in structured data.
7. Do not introduce deployment infrastructure while application functionality remains incomplete unless explicitly requested.
