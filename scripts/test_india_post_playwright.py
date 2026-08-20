"""
Controlled Playwright Browser Investigation for India Post Public Tracking.
Navigates to the public India Post tracking page in a real browser session
and inspects the rendered DOM for inputs, CAPTCHA, submit buttons, and tracking results.
"""
import os
import sys
import json
import time
from playwright.sync_api import sync_playwright

INDIA_POST_TRACKING_URL = "https://www.indiapost.gov.in/_layouts/15/dop.portal.tracking/trackconsignment.aspx"

def run_playwright_investigation(tracking_number: str = "EM740043207IN") -> dict:
    os.makedirs("uploads/poc", exist_ok=True)
    screenshot_path = "uploads/poc/india_post_browser.png"
    html_dump_path = "uploads/poc/india_post_browser.html"
    
    print("==================================================")
    print("PLAYWRIGHT BROWSER INVESTIGATION — INDIA POST")
    print(f"Target URL: {INDIA_POST_TRACKING_URL}")
    print(f"Tracking Number: {tracking_number}")
    print("==================================================\n")
    
    report = {
        "tracking_number": tracking_number,
        "target_url": INDIA_POST_TRACKING_URL,
        "browser": "Chromium (Headless)",
        "page_loaded": False,
        "page_title": "",
        "tracking_input_found": False,
        "tracking_input_selector": None,
        "submit_button_found": False,
        "submit_button_selector": None,
        "captcha_present": False,
        "captcha_selector": None,
        "captcha_type": None,
        "screenshot_saved": False,
        "html_saved": False,
        "classification": None,
        "explanation": "",
        "events_found": []
    }
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 800}
        )
        page = context.new_page()
        
        try:
            print("[*] Navigating to public tracking URL...")
            response = page.goto(INDIA_POST_TRACKING_URL, timeout=30000, wait_until="domcontentloaded")
            report["page_loaded"] = True
            report["page_title"] = page.title()
            print(f"[+] Page loaded successfully: '{page.title()}' (HTTP {response.status if response else 'Unknown'})")
            
            # Wait briefly for client-side scripts to settle
            page.wait_for_timeout(3000)
            
            # Save sanitized HTML
            sanitized_html = page.content()
            with open(html_dump_path, "w", encoding="utf-8") as f:
                f.write(sanitized_html)
            report["html_saved"] = True
            
            # Save screenshot
            page.screenshot(path=screenshot_path)
            report["screenshot_saved"] = True
            print(f"[+] Saved screenshot to: {screenshot_path}")
            
            # 1. Search for tracking number input
            track_selectors = [
                "input[id*='txtTrkNo']",
                "input[name*='txtTrkNo']",
                "input[id*='Consignment']",
                "input[placeholder*='Consignment']",
                "input[type='text']"
            ]
            for sel in track_selectors:
                if page.locator(sel).count() > 0:
                    report["tracking_input_found"] = True
                    report["tracking_input_selector"] = sel
                    print(f"[+] Found tracking input field: {sel}")
                    break
                    
            # 2. Search for Submit / Search button
            btn_selectors = [
                "input[id*='btnSearch']",
                "input[type='submit']",
                "button[id*='btnSearch']",
                "button:has-text('Track')",
                "button:has-text('Search')"
            ]
            for b_sel in btn_selectors:
                if page.locator(b_sel).count() > 0:
                    report["submit_button_found"] = True
                    report["submit_button_selector"] = b_sel
                    print(f"[+] Found submit button: {b_sel}")
                    break
                    
            # 3. Search for CAPTCHA elements
            captcha_img_selectors = [
                "img[id*='captcha' i]",
                "img[id*='Captcha' i]",
                "img[src*='captcha' i]",
                "input[id*='txtCaptcha' i]",
                "input[id*='captcha' i]"
            ]
            for c_sel in captcha_img_selectors:
                if page.locator(c_sel).count() > 0:
                    report["captcha_present"] = True
                    report["captcha_selector"] = c_sel
                    report["captcha_type"] = "Visual Image / Arithmetic Session Challenge"
                    print(f"[!] CAPTCHA element detected: {c_sel}")
                    break
                    
            # Classification
            if report["captcha_present"]:
                report["classification"] = "PUBLIC TRACKING WORKFLOW: BLOCKED BY CAPTCHA / ACCESS CONTROL"
                report["explanation"] = (
                    "The public India Post tracking portal loads in the browser with tracking input fields, "
                    "but enforces an image-based CAPTCHA verification challenge before queries can be processed. "
                    "In compliance with ADR-002, automated CAPTCHA bypass is strictly prohibited. "
                    "Therefore, automated public browser queries cannot proceed without an authorized API or provider integration."
                )
            elif report["tracking_input_found"] and report["submit_button_found"]:
                report["classification"] = "PUBLIC TRACKING WORKFLOW: USABLE WITHOUT ACCESS CONTROL BLOCK"
                report["explanation"] = "Tracking input and submit button are present without mandatory CAPTCHA challenges."
            else:
                report["classification"] = "PUBLIC TRACKING WORKFLOW: INSUFFICIENT DATA / UNRECOGNIZED DOM"
                report["explanation"] = "Page loaded, but tracking input elements could not be resolved."
                
        except Exception as e:
            print(f"[!] Browser navigation error: {e}")
            report["classification"] = "PUBLIC TRACKING WORKFLOW: INACCESSIBLE FROM CURRENT ENVIRONMENT"
            report["explanation"] = f"Navigation failed or timed out: {e}"
            
        browser.close()
        
    print("\n--- Playwright Investigation Report ---")
    print(json.dumps(report, indent=2))
    return report

if __name__ == "__main__":
    t_id = sys.argv[1] if len(sys.argv) > 1 else "EM740043207IN"
    run_playwright_investigation(t_id)
