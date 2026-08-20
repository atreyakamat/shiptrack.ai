"""
Detailed Inspection & Tracking Submission Test for India Post Homepage.
"""
import os
import sys
import json
import time
from playwright.sync_api import sync_playwright

def inspect_form_and_submit(tracking_number: str = "EM740043207IN"):
    os.makedirs("uploads/web_poc", exist_ok=True)
    report = {
        "tracking_number": tracking_number,
        "input_selector_found": None,
        "captcha_selector_found": None,
        "captcha_label": None,
        "submit_selector_found": None,
        "post_submit_url": None,
        "post_submit_title": None,
        "tracking_table_found": False,
        "raw_text_snippet": ""
    }

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--disable-blink-features=AutomationControlled", "--no-sandbox"]
        )
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            viewport={"width": 1366, "height": 768}
        )
        page = context.new_page()
        page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

        print("[*] Navigating to https://www.indiapost.gov.in/ ...")
        page.goto("https://www.indiapost.gov.in/", wait_until="load", timeout=30000)
        page.wait_for_timeout(3000)

        # Inspect all inputs
        inputs = page.locator("input").all()
        for inp in inputs:
            inp_id = inp.get_attribute("id") or ""
            inp_name = inp.get_attribute("name") or ""
            inp_type = inp.get_attribute("type") or ""
            inp_placeholder = inp.get_attribute("placeholder") or ""
            print(f"Input: id='{inp_id}' name='{inp_name}' type='{inp_type}' placeholder='{inp_placeholder}'")

            if "txtTrkNo" in inp_id or "Consignment" in inp_placeholder or "track" in inp_id.lower():
                report["input_selector_found"] = f"#{inp_id}" if inp_id else f"input[name='{inp_name}']"
            if "captcha" in inp_id.lower() or "captcha" in inp_name.lower():
                report["captcha_selector_found"] = f"#{inp_id}" if inp_id else f"input[name='{inp_name}']"

        # Check for CAPTCHA images / labels
        captcha_imgs = page.locator("img[id*='captcha' i], img[src*='captcha' i], img[id*='Captcha' i]").all()
        if captcha_imgs:
            print(f"[!] Found {len(captcha_imgs)} CAPTCHA images.")
            report["captcha_selector_found"] = "Image CAPTCHA element present"

        # Look for Track button
        btn = page.locator("input[type='submit'][value*='Track' i], button:has-text('Track Now'), input[id*='btnSearch' i]").first
        if btn.count() > 0:
            report["submit_selector_found"] = btn.get_attribute("id") or btn.get_attribute("value")
            print(f"[+] Found submit button: {report['submit_selector_found']}")

        page.screenshot(path="uploads/web_poc/form_inspection.png")
        print("[+] Saved form_inspection.png")

        browser.close()

    print("\n--- Form Inspection Report ---")
    print(json.dumps(report, indent=2))
    return report

if __name__ == "__main__":
    t_no = sys.argv[1] if len(sys.argv) > 1 else "EM740043207IN"
    inspect_form_and_submit(t_no)
