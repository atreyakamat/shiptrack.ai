"""
Isolated Proof-of-Concept for India Post Public Tracking Workflow Investigation.
Determines whether the publicly accessible India Post tracking page can return tracking data
without bypassing CAPTCHA, anti-bot controls, or authentication.
"""
import os
import sys
import json
import time
import requests
from bs4 import BeautifulSoup

INDIA_POST_TRACKING_URL = "https://www.indiapost.gov.in/_layouts/15/dop.portal.tracking/trackconsignment.aspx"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

def inspect_public_tracking_page(tracking_number: str = "EM740043207IN") -> dict:
    os.makedirs("uploads/poc", exist_ok=True)
    debug_html_path = "uploads/poc/india_post_public_page.html"
    
    print("==================================================")
    print("INDIA POST PUBLIC TRACKING INVESTIGATION")
    print(f"Target URL: {INDIA_POST_TRACKING_URL}")
    print(f"Tracking ID: {tracking_number}")
    print("==================================================\n")
    
    report = {
        "tracking_number": tracking_number,
        "target_url": INDIA_POST_TRACKING_URL,
        "http_status": None,
        "page_accessible": False,
        "form_fields_found": [],
        "captcha_required": False,
        "captcha_type": None,
        "bot_protection_detected": False,
        "automated_query_possible": False,
        "poc_status": "BLOCKED / INSUFFICIENT DATA",
        "events": [],
        "explanation": ""
    }
    
    try:
        session = requests.Session()
        session.headers.update({"User-Agent": USER_AGENT})
        
        print("[*] Fetching public tracking page...")
        response = session.get(INDIA_POST_TRACKING_URL, timeout=15)
        report["http_status"] = response.status_code
        
        if response.status_code == 200:
            report["page_accessible"] = True
            html_content = response.text
            
            with open(debug_html_path, "w", encoding="utf-8") as f:
                f.write(html_content)
                
            soup = BeautifulSoup(html_content, "html.parser")
            
            # Look for tracking input
            track_input = soup.find("input", {"id": lambda x: x and "txtTrkNo" in x}) or soup.find("input", {"name": lambda x: x and "Consignment" in x})
            if track_input:
                report["form_fields_found"].append(track_input.get("name") or track_input.get("id"))
                print(f"[+] Found tracking number input element: {track_input.get('id')}")
            
            # Look for CAPTCHA elements
            captcha_img = soup.find("img", {"id": lambda x: x and ("captcha" in x.lower() or "imgcaptcha" in x.lower())})
            captcha_input = soup.find("input", {"id": lambda x: x and ("captcha" in x.lower() or "txtcaptcha" in x.lower())})
            
            if captcha_img or captcha_input:
                report["captcha_required"] = True
                report["captcha_type"] = "Image / Arithmetic Challenge (Server-validated session token)"
                print(f"[!] CAPTCHA Protection Detected: {report['captcha_type']}")
            else:
                # Check for other security tokens
                viewstate = soup.find("input", {"id": "__VIEWSTATE"})
                if viewstate:
                    report["form_fields_found"].append("__VIEWSTATE")
            
            # Determine if automated query without CAPTCHA bypass is possible
            if report["captcha_required"]:
                report["automated_query_possible"] = False
                report["poc_status"] = "BLOCKED / CAPTCHA REQUIRED"
                report["explanation"] = (
                    "The public India Post tracking portal enforces a mandatory server-side CAPTCHA image challenge "
                    "on every consignment query. In compliance with ADR-002, CAPTCHA bypass is strictly prohibited. "
                    "Therefore, automated scraping via public web endpoints cannot proceed without external credentials or an authorized commercial API."
                )
            else:
                report["poc_status"] = "ACCESSIBLE_NO_CAPTCHA"
                report["automated_query_possible"] = True
                report["explanation"] = "Tracking form is accessible without CAPTCHA."
                
        else:
            report["explanation"] = f"HTTP request returned status {response.status_code}."
            
    except requests.exceptions.RequestException as req_err:
        print(f"[!] Network error connecting to India Post portal: {req_err}")
        report["poc_status"] = "NETWORK_ERROR / BLOCKED"
        report["explanation"] = f"Connection failed: {req_err}"
        
    print("\n--- POC Results ---")
    print(json.dumps(report, indent=2))
    return report

if __name__ == "__main__":
    track_id = sys.argv[1] if len(sys.argv) > 1 else "EM740043207IN"
    inspect_public_tracking_page(track_id)
