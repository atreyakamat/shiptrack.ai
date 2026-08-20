# Phase 3.1 Provider Adapter Readiness Report

**Product**: ShipTrack AI  
**Milestone**: Phase 3.1 — Carrier Adapter Architecture & Human-Assisted Web Tracking  
**Date**: 2026-08-20  
**Reference Document**: [`SHIPTRACK_AI_MASTER_PRD_ARCHITECTURE.md`](file:///C:/Projects/shiptrack.ai/SHIPTRACK_AI_MASTER_PRD_ARCHITECTURE.md)  
**Test Suite**: **103 / 103 passed (100% green)**  
**Compilation**: **0 errors across all modules (`python -m compileall backend frontend scripts tests`)**

---

## 1. Supported Carrier Adapters

The system implements the [`BaseCarrierAdapter`](file:///C:/Projects/shiptrack.ai/backend/carriers/base.py) contract with three distinct operational adapters:

```text
                                  BaseCarrierAdapter
                                          │
        ┌─────────────────────────────────┼─────────────────────────────────┐
        ▼                                 ▼                                 ▼
MockCarrierAdapter             AuthorizedTrackingAdapter            IndiaPostWebAdapter
(7 Simulated Scenarios)       (Commercial REST APIs)          (Human-Assisted Playwright)
Default / Test Runner         TrackingMore / Ship24           Direct India Post Portal
```

---

## 2. Human-Assisted Web Tracking Adapter (`IndiaPostWebAdapter`)

Implemented in [`backend/carriers/india_post_web.py`](file:///C:/Projects/shiptrack.ai/backend/carriers/india_post_web.py):
*   **Workflow**:
    1. User triggers tracking sync for an India Post consignment (`EM...IN`).
    2. Playwright launches an interactive Chromium session and navigates to `https://www.indiapost.gov.in/`.
    3. The tracking number is automatically pre-filled into the consignment input field.
    4. The CAPTCHA input field is highlighted and focused for user entry.
    5. The human user enters the visible visual/arithmetic CAPTCHA and clicks **Track Now**.
    6. Playwright captures the rendered DOM result table (Date, Time, Office, Status).
    7. Data is parsed via [`CarrierNormalizer`](file:///C:/Projects/shiptrack.ai/backend/carriers/normalizer.py) and ingested into SQLite via [`TrackingService.deduplicate_events`](file:///C:/Projects/shiptrack.ai/backend/services/tracking_service.py).
*   **Compliance**: 100% compliant with **ADR-002** (zero CAPTCHA bypassing or unauthorized cracking).

---

## 3. Provider Configuration & Selection

Configured via environment variables:
*   `TRACKING_PROVIDER=mock`: Default offline simulation mode (zero network calls).
*   `TRACKING_PROVIDER=web` (or `india_post_web`): Human-assisted interactive Playwright tracking.
*   `TRACKING_PROVIDER=authorized`: Commercial REST API integration (requires `TRACKING_API_KEY`).
*   `TRACKING_DEMO_MODE=true`: Enforces mock mode regardless of provider setting for test isolation.

---

## 4. Canonical Event Schema & Normalization

The normalization layer [`backend/carriers/normalizer.py`](file:///C:/Projects/shiptrack.ai/backend/carriers/normalizer.py) converts both web tables and API JSON payloads into ShipTrack's canonical schema:

```python
{
    "tracking_number": str,
    "status": str,              # BOOKED | IN_TRANSIT | ARRIVED_AT_FACILITY | OUT_FOR_DELIVERY | DELIVERED | DELAYED | RETURNED | UNKNOWN
    "event_date": str,          # DD/MM/YYYY
    "event_time": str,          # HH:MM AM/PM
    "location": Optional[str],  # Raw facility string (e.g., "Panaji NSH")
    "description": Optional[str],
    "raw_status": Optional[str]
}
```

---

## 5. Test Suite Verification

*   **Total Tests**: **103 passing tests** across 16 test modules.
*   **New Web Adapter Tests** in [`tests/test_india_post_web_adapter.py`](file:///C:/Projects/shiptrack.ai/tests/test_india_post_web_adapter.py):
    *   `test_web_adapter_tracking_number_validation`: Postal syntax checks.
    *   `test_web_adapter_extract_table_data`: 4-column event table DOM parsing.
    *   `test_web_adapter_extract_3col_table`: 3-column event table DOM parsing.
    *   `test_web_adapter_empty_table_returns_empty_events`: Empty result handling.
    *   `test_tracking_service_provider_selection_web`: Routing in `TrackingService`.

---

## 6. Current Status

```text
FINAL STATUS:
INDIA POST WEB TRACKING ADAPTER IMPLEMENTED & TESTED (103/103 TESTS GREEN)
```
