"""
Playwright Web Automation Investigation for India Post Public Tracking.
Tests navigating to the public tracking page using realistic browser configurations,
session initialization, and standard form interactions.
"""
import os
import sys
import json
import time
from playwright.sync_api import sync_playwright

INDIA_POST_URLS = [
    "https://www.indiapost.gov.in/",
    "https://www.indiapost.gov.in/_layouts/15/dop.portal.tracking/trackconsignment.aspx",
    "https://www.indiapost.gov.in/VAS/Pages/IndiaPostHome.aspx"
]

def test_web_automation(tracking_number: str = "EM740043207IN") -> dict:
    os.makedirs("uploads/web_poc", exist_ok=True)
    report = {
        "tracking_number": tracking_number,
        "attempts": [],
        "successful_url": None,
        "tracking_form_found": False,
        "captcha_required": False,
        "result_extracted": False,
        "events": [],
        "explanation": ""
    }

    print("==================================================")
    print("INDIA POST PUBLIC WEB AUTOMATION INVESTIGATION")
    print(f"Tracking Number: {tracking_number}")
    print("==================================================\n")

    with sync_playwright() as p:
        # Launch Chromium with realistic flags to mimic normal user browser
        browser = p.chromium.launch(
            headless=True,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-infobars"
            ]
        )
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            viewport={"width": 1366, "height": 768},
            locale="en-IN",
            timezone_id="Asia/Kolkata"
        )
        
        page = context.new_page()
        # Remove navigator.webdriver flag
        page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

        for url in INDIA_POST_URLS:
            attempt_info = {"url": url, "status": None, "error": None}
            print(f"[*] Trying URL: {url}...")
            try:
                response = page.goto(url, timeout=25000, wait_until="load")
                attempt_info["status"] = response.status if response else "No response"
                print(f"[+] Loaded: {url} (HTTP {attempt_info['status']}) - Title: '{page.title()}'")
                
                # Check for tracking input box on homepage or tracking page
                inputs = page.locator("input[type='text']").all()
                print(f"[+] Found {len(inputs)} text input elements on page.")
                
                # Take screenshot for visual inspection
                screen_path = f"uploads/web_poc/{url.replace('https://', '').replace('/', '_').replace(':', '_')}.png"
                page.screenshot(path=screen_path)
                print(f"[+] Saved screenshot: {screen_path}")
                
                # Check for consignment tracking box
                track_box = page.locator("input[placeholder*='Consignment' i], input[id*='txtTrkNo' i], input[id*='Track' i], input[name*='Track' i]")
                if track_box.count() > 0:
                    report["tracking_form_found"] = True
                    report["successful_url"] = url
                    print(f"[!] Tracking input field located on {url}")
                    
                report["attempts"].append(attempt_info)
                break # Reached a working page
            except Exception as e:
                attempt_info["error"] = str(e)
                print(f"[-] Failed {url}: {e}")
                report["attempts"].append(attempt_info)

        browser.close()

    print("\n--- Summary Report ---")
    print(json.dumps(report, indent=2))
    return report

if __name__ == "__main__":
    t_no = sys.argv[1] if len(sys.argv) > 1 else "EM740043207IN"
    test_web_automation(t_no)
