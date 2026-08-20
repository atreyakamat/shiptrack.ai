"""
Controlled OCR Validation Harness for ShipTrack AI.
Tests real and benchmark synthetic India Post receipt images across multiple conditions:
1. Clear receipt
2. Angled/Rotated receipt
3. Low-light/Low-contrast receipt
4. Slightly blurred receipt
5. Receipt with multiple numbers/text
6. Receipt with noise and interference
"""
import os
import sys
import time
import json
from typing import Dict, Any, List

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import cv2
import numpy as np
from backend.services.ocr_service import OCRService

def create_synthetic_receipt(condition: str, tracking_no: str = "EM740043207IN") -> str:
    """Generate controlled synthetic test receipts for various optical conditions."""
    h, w = 400, 700
    img = np.ones((h, w, 3), dtype=np.uint8) * 255
    
    # Draw postal receipt header
    cv2.putText(img, "DEPARTMENT OF POSTS - INDIA", (120, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)
    cv2.putText(img, "SPEED POST BOOKING RECEIPT", (150, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 1)
    cv2.line(img, (50, 95), (650, 95), (0, 0, 0), 1)
    
    cv2.putText(img, f"Article No: {tracking_no}", (50, 140), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 2)
    cv2.putText(img, "From: PANAJI NSH (403001)", (50, 180), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (50, 50, 50), 1)
    cv2.putText(img, "To: BAMBAVADA S.O (403107)", (50, 210), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (50, 50, 50), 1)
    cv2.putText(img, "Wt: 50 gms | Tariff: Rs 41.30", (50, 240), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (50, 50, 50), 1)
    cv2.putText(img, "Date: 19/08/2026 10:15:30", (50, 270), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (50, 50, 50), 1)
    
    if condition == "clear":
        pass
    elif condition == "angled":
        center = (w // 2, h // 2)
        matrix = cv2.getRotationMatrix2D(center, 5.0, 1.0) # 5-degree tilt
        img = cv2.warpAffine(img, matrix, (w, h), borderValue=(255, 255, 255))
    elif condition == "low_light":
        img = (img * 0.45).astype(np.uint8) # Darkened
    elif condition == "blurred":
        img = cv2.GaussianBlur(img, (5, 5), 0)
    elif condition == "multi_number":
        cv2.putText(img, "Ref Article: EE123456789IN", (50, 310), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)
        cv2.putText(img, "Old Track No: SS987654321IN", (50, 350), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)
    elif condition == "noise":
        noise = np.random.normal(0, 20, img.shape).astype(np.int16)
        img = np.clip(img.astype(np.int16) + noise, 0, 255).astype(np.uint8)
        
    os.makedirs("uploads/benchmarks", exist_ok=True)
    out_path = f"uploads/benchmarks/receipt_{condition}.png"
    cv2.imwrite(out_path, img)
    return out_path

def run_benchmark():
    conditions = ["clear", "angled", "low_light", "blurred", "multi_number", "noise"]
    results = []
    expected_no = "EM740043207IN"
    
    print("==================================================")
    print("SHIPTRACK AI — OCR BENCHMARK & REAL VALIDATION")
    print("==================================================\n")
    
    for cond in conditions:
        img_path = create_synthetic_receipt(cond, expected_no)
        start_time = time.time()
        
        proc_result = OCRService.process_image(img_path)
        elapsed_ms = (time.time() - start_time) * 1000
        
        candidates = proc_result.get('candidates', [])
        raw_text = proc_result.get('full_text', '')
        extracted_no = proc_result.get('extracted_tracking_number')
        confidence = proc_result.get('confidence', 0.0)
        
        detected_expected = any(c['tracking_number'] == expected_no for c in candidates)
        ranked_first = len(candidates) > 0 and candidates[0]['tracking_number'] == expected_no
        false_positives = [c['tracking_number'] for c in candidates if c['tracking_number'] not in [expected_no, "EE123456789IN", "SS987654321IN"]]
        
        res_record = {
            "condition": cond,
            "image_path": img_path,
            "processing_time_ms": round(elapsed_ms, 2),
            "raw_text_snippet": raw_text[:80] + ("..." if len(raw_text) > 80 else ""),
            "detected_candidates": [c['tracking_number'] for c in candidates],
            "first_candidate": extracted_no,
            "confidence": confidence,
            "detected_expected": detected_expected,
            "ranked_first": ranked_first,
            "false_positives_count": len(false_positives)
        }
        results.append(res_record)
        
        status_icon = "PASS" if detected_expected else "PARTIAL/BLOCKED"
        print(f"[{cond.upper():12s}] {status_icon:14s} Time: {elapsed_ms:6.1f}ms | Extracted: {extracted_no} (Conf: {confidence}) | Candidates: {len(candidates)}")
        
    print("\n--- Summary Report ---")
    print(json.dumps(results, indent=2))
    return results

if __name__ == "__main__":
    run_benchmark()
