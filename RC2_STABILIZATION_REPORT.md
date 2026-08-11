# ShipTrack AI — RC2 Stabilization Report

This document serves as the official record for the `v1.0.0-rc2` stabilization pass, resolving critical rendering and data integrity issues identified during RC1 browser usage.

## 1. Bugs Discovered
1. **Raw HTML Leakage:** Streamlit was interpreting indented HTML strings wrapped in `st.markdown(..., unsafe_allow_html=True)` as Markdown code blocks, exposing raw HTML to the user in the Shipment Details and Timeline views.
2. **"None" Value Leaks:** Missing database values (e.g. absent `description` or `current_location`) were serialized to JSON `null`. In Python, the frontend dictionary returned `None`, and printing it directly to Streamlit resulted in literal "None" strings across the UI.
3. **Data Contract Fragmentation:** Tracking events were scattered between `event_date`, `event_time`, and `event_timestamp`, leading to disjointed data structures.
4. **Error Traceback Leaks:** API client HTTP errors (401, 404, 500) were being caught but passed through generically or failing during `.json()` parsing, resulting in raw exceptions being shown on the screen.

## 2. Root Causes
- **Streamlit Markdown Engine:** The markdown engine fundamentally opposes indented HTML inside strings. 
- **Python Dictionary `get()` Limitation:** Using `data.get('description', 'Fallback')` fails to provide the fallback if the key exists but its value is literally `None` (which `jsonify` correctly created from SQL `NULL`).
- **Database Migrations vs Code Scaffold:** The old backend tracking adapters were populating date/time separately while the unified standard needed ISO 8601 strings.

## 3. Fixes
- Replaced `.get(x, fallback)` with the `or 'Fallback'` logical evaluation across the entire frontend to robustly eradicate `None`.
- Eliminated `st.markdown(..., unsafe_allow_html=True)` for all complex DOM construction, adopting the much safer `st.html()` Streamlit 1.34+ primitive which bypasses Markdown completely.
- Upgraded the API Client exception handling block to intercept specific HTTP Status codes (404, 401, 429, 503) and convert them to clean, user-facing error messages (e.g. "Your session has expired. Please sign in again").

## 4. API Contract Changes
Documented formally in `docs/API_CONTRACT.md`.
- Established `{success: true, data: ...}` standard envelopes.
- `TrackingEvent` now computes and guarantees `event_timestamp` in ISO 8601 string format, retiring the usage of standalone `event_date` and `event_time` fields from frontend consumption.

## 5. Frontend Changes
- `api_client.py`: Implemented robust JSON parsing and HTTP Code-to-User-String translation maps.
- `shipment_detail.py`: Converted all metric layouts and layout columns to `st.html()`. Added gracefully degraded fallback text.
- `timeline.py` & `shipment_card.py`: Safely parse `event_timestamp`. Strip "None" text.

## 6. Backend Changes
- `models/tracking_event.py`: Updated `to_dict()` serialization to dynamically construct `event_timestamp` from legacy components if needed, emitting standard ISO strings.

## 7. Tests Added
- `test_api_contracts.py` added to `tests/`.
- Included `test_api_success_envelope`, `test_api_error_envelope` to validate envelope structures.
- Included `test_tracking_event_serialization`, `test_shipment_serialization` to guarantee timestamp behavior and proper handling of null fields in dictionaries.

## 8. Full Test Result
```text
============================= test session starts =============================
tests/test_api_contracts.py::test_api_success_envelope PASSED            [ 25%]
tests/test_api_contracts.py::test_api_error_envelope PASSED              [ 50%]
tests/test_api_contracts.py::test_tracking_event_serialization PASSED    [ 75%]
tests/test_api_contracts.py::test_shipment_serialization PASSED          [100%]
======================= 4 passed, 12 warnings in 11.48s =======================
```

## 9. Browser Verification Result
- Server booted successfully on port `8501`.
- Streamlit application successfully handled empty states, rendering all custom UI components via DOM injection (`st.html`) without code block formatting.
- Map component ignores completely null coordinates without throwing `folium` exceptions.
- API Client handles unauthorized connections gracefully.
- All acceptance criteria have passed.

## 10. Remaining Known Issues
- Currently, the local SQLite database holds older schema data in some cases; a clean migration or wipe may be needed for edge-case tracking events containing malformed strings, though the frontend now masks this safely.
- PayU Refund Validation is formally deferred to a subsequent milestone as architecture is currently frozen for RC2.
