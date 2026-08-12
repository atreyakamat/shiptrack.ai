import requests
import json
import time

BASE_URL = "http://localhost:5000/api"
RESULTS = []
AUTH_TOKEN = None

def log_req(method, endpoint, result, status_code, details=""):
    RESULTS.append({
        "METHOD": method,
        "ENDPOINT": endpoint,
        "STATUS": status_code,
        "RESULT": result,
        "DETAILS": details
    })
    print(f"[{method}] {endpoint} - {status_code} - {result}")
    
def make_req(method, endpoint, payload=None, expect=None):
    headers = {}
    if AUTH_TOKEN:
        headers["Authorization"] = f"Bearer {AUTH_TOKEN}"
        
    url = f"{BASE_URL}{endpoint}"
    try:
        if method == "GET":
            res = requests.get(url, headers=headers, timeout=5)
        elif method == "POST":
            res = requests.post(url, json=payload, headers=headers, timeout=5)
        elif method == "PUT":
            res = requests.put(url, json=payload, headers=headers, timeout=5)
        elif method == "DELETE":
            res = requests.delete(url, headers=headers, timeout=5)
            
        is_success = True
        if expect and res.status_code not in expect:
            is_success = False
            
        log_req(method, endpoint, "SUCCESS" if is_success else "FAILED", res.status_code, res.text[:200])
        return res
    except Exception as e:
        log_req(method, endpoint, "FAILED (Exception)", "ERROR", str(e))
        return None

print("Starting Manual End-To-End Simulation...")

# 1. Health check
make_req("GET", "/health", expect=[200])

# 2. Register
register_res = make_req("POST", "/auth/register", {"email": "manualtest2@shiptrack.ai", "password": "password123"}, expect=[201, 409])

# 3. Login
login_res = make_req("POST", "/auth/login", {"email": "manualtest2@shiptrack.ai", "password": "password123"}, expect=[200])
if login_res and login_res.status_code == 200:
    AUTH_TOKEN = login_res.json().get("data", {}).get("token")

# 4. Invalid Login
make_req("POST", "/auth/login", {"email": "manualtest2@shiptrack.ai", "password": "wrongpassword"}, expect=[401])

# 5. Dashboard / Shipments list
make_req("GET", "/shipments", expect=[200])

# 6. Add Valid Shipment (India Post)
add_valid = make_req("POST", "/shipments", {"tracking_number": "EM998877665IN", "carrier": "india_post", "description": "Test E2E"}, expect=[201])
shipment_id = None
if add_valid and add_valid.status_code == 201:
    shipment_id = add_valid.json().get("data", {}).get("id")

# 7. Add Duplicate Shipment (India Post)
make_req("POST", "/shipments", {"tracking_number": "EM998877665IN", "carrier": "india_post", "description": "Duplicate Test"}, expect=[409])

# 8. Add Invalid Tracking Number
make_req("POST", "/shipments", {"tracking_number": "12345", "carrier": "india_post", "description": "Invalid"}, expect=[422, 400])

# 9. Provider Unavailable Handling
make_req("POST", "/shipments", {"tracking_number": "EM100000099IN", "carrier": "india_post", "description": "Provider Error Test"}, expect=[201])

# 10. Get Shipment Detail
if shipment_id:
    make_req("GET", f"/shipments/{shipment_id}", expect=[200])

# 11. AI Insights
if shipment_id:
    make_req("GET", f"/ai/{shipment_id}/summary", expect=[200])

# 12. Analytics
make_req("GET", "/analytics", expect=[200])

# 13. Notifications
make_req("GET", "/notifications", expect=[200])

# 14. OCR 
make_req("POST", "/ocr", payload={}, expect=[400])

# 15. Logout (We don't strictly have a stateful logout backend, but we can hit health again)
AUTH_TOKEN = None
make_req("GET", "/shipments", expect=[401])

# Save results to a file
with open("e2e_results.json", "w") as f:
    json.dump(RESULTS, f, indent=2)

print("Finished simulation.")
