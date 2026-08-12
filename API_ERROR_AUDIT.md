# ShipTrack AI - API Error Audit Report

## Executive Summary
This audit identifies all API error handling issues in the ShipTrack AI application, focusing on the "ShipTrack AI encountered an internal server error" symptom on the Add New Shipment page.

## Phase 1: Reproduced Current Error

### Test Case: Add Shipment with EM740043207IN
- **Frontend Carrier**: "India Post" 
- **Backend Expected**: "india_post"
- **Result**: With current `TRACKING_PROVIDER=mock`, shipment creates successfully (201) because MockCarrierAdapter is used
- **Root Cause Potential**: When `TRACKING_PROVIDER=india_post`, the IndiaPostAdapter raises `NotImplementedError` causing 500

### HTTP Trace
```
POST /api/shipments
Headers: Authorization: Bearer <token>, Content-Type: application/json
Payload: {"tracking_number":"EM740043207IN","carrier":"India Post","category":"General","description":"Test shipment","priority":"Normal","notes":"API error debugging test"}
Response: 201 Created (with mock provider)
```

## Phase 2: Complete Add Shipment Flow Trace

```
Streamlit Add Shipment page (add_shipment.py)
    ↓
frontend/api_client.py -> create_shipment(data)
    ↓
HTTP POST /api/shipments
    ↓
backend/routes/shipments.py -> create_shipment()
    ↓
@token_required (auth.py) -> validates JWT, sets g.current_user
    ↓
ShipmentService.create_shipment(g.current_user.id, data)
    ↓
Validates tracking number (validators.py)
    ↓
Checks duplicate (carrier + tracking_number unique constraint)
    ↓
Creates Shipment, commits to DB
    ↓
TrackingService.refresh_shipment(shipment.id) [try/except, decoupled]
    ↓
Returns shipment.to_dict() 201
```

## Phase 3: Request Payload Issues

### Carrier Mapping Mismatch
- **Frontend sends**: `"carrier": "India Post"` (from selectbox options)
- **Backend expects**: `"india_post"` (validated in `validators.py:21`, `tracking_service.py:24`)
- **Result**: `validate_carrier("India Post")` returns `False`
- **Impact**: Backend uses `MockCarrierAdapter` instead of `IndiaPostAdapter` when provider is not mock

### Field Name Verification
| Frontend Field | Backend Field | Match |
|---|---|---|
| tracking_number | tracking_number | ✅ |
| carrier | carrier | ❌ (label vs code) |
| category | category | ✅ |
| description | description | ✅ |
| priority | priority | ✅ |
| notes | notes | ✅ |

## Phase 4: Tracking Number Validation

### Current Validation (`validators.py:6-12`)
```python
def validate_tracking_number(number: str, carrier: str = 'india_post') -> bool:
    if not number: return False
    number = normalize_tracking_number(number)
    if carrier == 'india_post':
        return bool(re.match(r'^[A-Z]{2}\d{9}IN$', number))
    return True
```

### Test Results
| Input | Expected | Actual |
|---|---|---|
| EM740043207IN | Valid | ✅ Valid |
| ABC | Invalid | ✅ Invalid |
| 123 | Invalid | ✅ Invalid |
| EM740043207 | Invalid | ✅ Invalid |
| EM740043207XX | Invalid | ✅ Invalid |
| "" | Invalid | ✅ Invalid |
| "  " | Invalid | ✅ Invalid |
| em740043207in | Valid (normalized) | ✅ Valid |
| "EM 740043207 IN" | Valid (normalized) | ✅ Valid |

**Issue**: Validation errors return 422 but carrier mismatch doesn't trigger validation error - it silently falls back to mock.

## Phase 5: Carrier Validation

### Current Implementation
```python
# validators.py:20-22
def validate_carrier(carrier: str) -> bool:
    supported_carriers = ['india_post', 'mock']
    return carrier in supported_carriers

# tracking_service.py:19-26
def get_carrier_adapter(carrier: str):
    provider = os.getenv('TRACKING_PROVIDER', 'mock')
    demo_mode = os.getenv('TRACKING_DEMO_MODE', 'true').lower() == 'true'
    if demo_mode or provider == 'mock' or carrier == 'mock':
        return MockCarrierAdapter()
    if carrier == 'india_post':
        return IndiaPostAdapter()
    return MockCarrierAdapter()
```

### Problem
- Frontend sends "India Post" (display label)
- Backend checks for "india_post" (internal code)
- No mapping layer exists
- **Fix Required**: Map frontend labels to backend codes

## Phase 6: Database Constraints

### Shipment Model Constraints
```python
# shipment.py:34-35
__table_args__ = (
    db.UniqueConstraint('carrier', 'tracking_number', name='uq_carrier_tracking'),
)
```

### Required Fields (nullable=False)
- user_id (FK to user.id)
- tracking_number (String(20))
- carrier (String(50), default='india_post')

### All Fields Provided by Frontend?
- ✅ tracking_number
- ❌ carrier (mismatch: "India Post" vs "india_post")
- ✅ category (default='general')
- ✅ description (nullable)
- ✅ priority (default='normal')
- ✅ notes (nullable)
- ✅ status (default='BOOKED')
- ✅ user_id (from g.current_user)

## Phase 7: User Ownership

### Flow Verification
```
JWT -> token_required (auth.py) -> g.current_user = User.query.get(data['user_id'])
    ↓
ShipmentService.create_shipment(g.current_user.id, data)
    ↓
Shipment(user_id=user_id, ...)
```
✅ Correct - never accepts user_id from request body

## Phase 8: Duplicate Tracking Numbers

### Current Handling
```python
# shipment_service.py:22-25
existing = Shipment.query.filter_by(user_id=user_id, tracking_number=tracking_num, carrier=carrier).first()
if existing:
    raise ValueError("Shipment already exists")

# shipments.py:47-51
except ValueError as ve:
    if "already exists" in str(ve).lower():
        return jsonify({'success': False, 'error': {'code': 'DUPLICATE_SHIPMENT', 'message': "This tracking number is already in your shipments."}}), 409
```

### Test Result: ✅ Returns 409 with DUPLICATE_SHIPMENT code

## Phase 9: India Post Adapter Behavior

### Current Code (`india_post.py:6-10`)
```python
def track(self, tracking_number: str) -> Dict[str, Any]:
    if not self.validate_tracking_number(tracking_number):
        raise ValueError(f"Invalid India Post tracking number: {tracking_number}")
    raise NotImplementedError('Live India Post tracking requires an authorized tracking integration.')
```

### Critical Issue
When `TRACKING_PROVIDER=india_post` and carrier is "india_post":
1. Shipment created successfully
2. `TrackingService.refresh_shipment()` called
3. `IndiaPostAdapter.track()` raises `NotImplementedError`
4. Caught in `TrackingService.refresh_shipment()` lines 157-179
5. Logs error, creates RefreshLog with status='error'
6. Returns `{'status': 'error', 'events_added': 0}`

### In Create Shipment Route (`shipments.py:39-45`)
```python
try:
    TrackingService.refresh_shipment(shipment.id)
except Exception as refresh_err:
    logger.warning(f"Initial tracking refresh failed for {shipment.id}, but shipment was saved: {refresh_err}")
```
✅ **Decoupled** - shipment creation succeeds even if tracking fails

### But: `/tracking/refresh` endpoint returns 500
```python
# tracking.py:21-23
result = TrackingService.refresh_shipment(id)
if result.get('status') == 'error':
    return jsonify({'success': False, 'error': {'code': 'REFRESH_ERROR', 'message': result.get('error_message', 'Unknown error')}}), 500
```

## Phase 10: Transaction Management

### Issues Found
1. **TrackingService.refresh_shipment()**: Multiple `db.session.commit()` calls (lines 84, 116, 118, 182) - could cause issues if exception occurs between commits
2. **ShipmentService.create_shipment()**: Single commit after add - ✅ Good
3. **Some routes missing rollback**: Notifications routes have rollback, others don't explicitly
4. **Session poisoning**: Need to test failed request followed by successful request

## Phase 11: All API Routes Inventory

| Method | Path | Auth | Success | 400 | 401 | 403 | 404 | 409 | 422 | 429 | 500 | 503 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| POST | /api/auth/register | ❌ | 201 | ✅ | - | - | - | ✅ | - | ✅ | ❌ | - |
| POST | /api/auth/login | ❌ | 200 | ✅ | - | - | - | - | - | ✅ | ❌ | - |
| GET | /api/shipments | ✅ | 200 | - | ✅ | - | - | - | - | ✅ | ❌ | - |
| POST | /api/shipments | ✅ | 201 | - | ✅ | - | - | ✅ | ✅ | ✅ | ❌ | - |
| GET | /api/shipments/<id> | ✅ | 200 | - | ✅ | - | ✅ | - | - | ✅ | ❌ | - |
| PUT | /api/shipments/<id> | ✅ | 200 | - | ✅ | - | ✅ | - | - | ✅ | ❌ | - |
| DELETE | /api/shipments/<id> | ✅ | 200 | - | ✅ | - | ✅ | - | - | ✅ | ❌ | - |
| POST | /api/shipments/<id>/archive | ✅ | 200 | - | ✅ | - | ✅ | - | - | ✅ | ❌ | - |
| POST | /api/shipments/<id>/refresh | ✅ | 200 | - | ✅ | - | ✅ | - | - | ✅ | ❌ | - |
| POST | /api/shipments/refresh-all | ✅ | 202 | - | ✅ | - | - | - | - | ✅ | ❌ | - |
| GET | /api/shipments/<id>/history | ✅ | 200 | - | ✅ | - | ✅ | - | - | ✅ | ❌ | - |
| GET | /api/ai/<id>/summary | ✅ | 200 | - | ✅ | - | ✅ | - | - | ✅ | ❌ | - |
| POST | /api/ai/<id>/generate | ✅ | 200 | - | ✅ | - | ✅ | - | - | ✅ | ❌ | - |
| GET/POST | /api/ai/insights | ✅ | 200 | - | ✅ | - | - | - | - | ✅ | ❌ | - |
| GET | /api/analytics | ✅ | 200 | - | ✅ | - | - | - | - | ✅ | ❌ | - |
| GET | /api/analytics/overview | ✅ | 200 | - | ✅ | - | - | - | - | ✅ | ❌ | - |
| GET | /api/analytics/export | ✅ | 200 | - | ✅ | - | - | - | - | ✅ | ❌ | - |
| POST | /api/ocr | ✅ | 200 | ✅ | ✅ | - | - | - | - | ✅ | ❌ | - |
| POST | /api/ocr/confirm | ✅ | 201 | - | ✅ | - | ✅ | - | - | ✅ | ❌ | - |
| GET | /api/notifications | ✅ | 200 | - | ✅ | - | - | - | - | ✅ | ❌ | - |
| POST | /api/notifications/<id>/read | ✅ | 200 | - | ✅ | - | ✅ | - | - | ✅ | ❌ | - |
| POST | /api/notifications/read-all | ✅ | 200 | - | ✅ | - | - | - | - | ✅ | ❌ | - |
| GET | /api/notifications/preferences | ✅ | 200 | - | ✅ | - | - | - | - | ✅ | ❌ | - |
| PUT | /api/notifications/preferences/<type> | ✅ | 200 | - | ✅ | - | ✅ | - | - | ✅ | ❌ | - |
| GET | /api/health | ❌ | 200 | - | - | - | - | - | - | - | - | - |

## Phase 12: All 500 Error Sources

### Generic Exception Handlers Returning 500
1. **shipments.py:27-29, 52-54, 67-69, 80-82, 92-94, 104-106** - Various endpoints
2. **tracking.py:25-27, 36-38, 48-50** - Refresh endpoints
3. **ai.py:28-30, 43-45, 55-57** - AI endpoints (expose `str(e)`)
4. **analytics.py:24-26, 34-36, 55-57** - Analytics endpoints (expose `str(e)`)
5. **ocr.py:65-67, 93-95** - OCR endpoints (expose `str(e)`)
6. **notifications.py:23-24, 34-35, 43-44, 52-53, 73-75** - Notification endpoints

### Issues
- ❌ `ai.py`, `analytics.py`, `ocr.py` expose `str(e)` in production response
- ❌ No request correlation ID
- ❌ Inconsistent error codes
- ✅ Most log the exception
- ✅ Most rollback database (where applicable)

## Phase 13: Error Format Standardization

### Current Format (Good)
```json
{
    "success": false,
    "error": {
        "code": "ERROR_CODE",
        "message": "Human-readable message"
    }
}
```

### Issues
- Some endpoints return `str(e)` instead of safe message
- No standard error code enum
- Missing PROVIDER_UNAVAILABLE, TRACKING_ERROR codes

## Phase 14: Frontend Error Parsing (`api_client.py:42-90`)

### Current Handling
- ✅ Parses backend error format
- ✅ Maps status codes to user messages
- ❌ "India Post" carrier not mapped to "india_post"
- ❌ Form data cleared on error (Streamlit form behavior)

### Missing Mappings
- 422: "Some shipment information is invalid." (generic)
- 503: "The tracking provider is currently unavailable."

## Phase 15-16: Logging & Correlation ID

### Current Logging
- Uses standard `logger.error()` with exception message
- ❌ No request ID/correlation ID
- ❌ No timestamp, endpoint, method, user ID in structured format
- ✅ No secrets logged

## Phase 17: Frontend UX (`add_shipment.py`)

### Issues
- ❌ Form clears on error (Streamlit form_submit_button behavior)
- ❌ No field-level validation feedback
- ✅ Shows error message

## Phase 18-21: Test Matrix & Provider Failure

### Not Yet Tested
Need to test all 20 scenarios from the matrix.

## Key Root Causes Identified

### 1. **Carrier Label/Code Mismatch** (HIGH)
- Frontend: "India Post" → Backend expects: "india_post"
- Causes silent fallback to MockCarrierAdapter
- When provider=india_post, this could cause unexpected behavior

### 2. **Error Message Exposure** (HIGH)
- AI, Analytics, OCR routes return `str(e)` in production
- Exposes stack traces, file paths, internal details

### 3. **Missing Error Codes** (MEDIUM)
- No PROVIDER_UNAVAILABLE, TRACKING_ERROR, OCR_ERROR codes
- Inconsistent handling across endpoints

### 4. **Transaction Session Poisoning Risk** (MEDIUM)
- Multiple commits in TrackingService.refresh_shipment
- Need to verify session recovery after failed request

### 5. **No Request Correlation ID** (LOW)
- Makes production debugging difficult

### 6. **Frontend Form Data Loss on Error** (LOW)
- Streamlit form clears on submit, even on error

## Files Requiring Fixes

1. `frontend/pages/add_shipment.py` - Map carrier labels to codes
2. `backend/utils/validators.py` - Add carrier label mapping
3. `backend/routes/ai.py` - Sanitize error messages
4. `backend/routes/analytics.py` - Sanitize error messages
5. `backend/routes/ocr.py` - Sanitize error messages
6. `backend/routes/tracking.py` - Fix 500 on provider error
7. `backend/services/tracking_service.py` - Improve transaction handling
8. `backend/utils/auth.py` - Add request ID
9. `frontend/api_client.py` - Add 422, 503 mappings
10. All route files - Standardize error codes