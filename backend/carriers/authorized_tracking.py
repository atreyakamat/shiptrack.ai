"""
Authorized Tracking Provider Adapter for ShipTrack AI.
Integrates with legitimate external tracking APIs (Official India Post / Licensed Aggregators)
using credentials supplied strictly through environment variables.
"""
import os
import re
import logging
from typing import Dict, Any, List, Optional
import requests
from .base import BaseCarrierAdapter
from .normalizer import CarrierNormalizer

logger = logging.getLogger(__name__)

class AuthorizedTrackingAdapter(BaseCarrierAdapter):
    def __init__(self, api_key: Optional[str] = None, api_url: Optional[str] = None, provider_name: Optional[str] = None):
        self.api_key = api_key or os.getenv('TRACKING_API_KEY', '')
        self.api_url = api_url or os.getenv('TRACKING_API_URL', '')
        self.provider_name = (provider_name or os.getenv('TRACKING_PROVIDER_NAME', 'trackingmore')).lower()

    def authenticate(self) -> bool:
        """Validates that valid API credentials are provided in the environment."""
        if not self.api_key or not self.api_key.strip():
            raise ValueError("Live carrier tracking requires valid API credentials configured in TRACKING_API_KEY.")
        return True

    def validate_tracking_number(self, tracking_number: str) -> bool:
        if not tracking_number:
            return False
        # Standard India Post / Universal Postal Union (UPU S10) pattern
        return bool(re.match(r'^[A-Z]{2}[0-9]{9}[A-Z]{2}$', tracking_number.strip().upper()))

    def normalize_status(self, raw_status: str) -> str:
        return CarrierNormalizer.normalize_status(raw_status)

    def track(self, tracking_number: str) -> Dict[str, Any]:
        """Fetches live tracking data from the authorized provider."""
        tracking_number = tracking_number.strip().upper()
        if not self.validate_tracking_number(tracking_number):
            raise ValueError(f"Invalid tracking number format: {tracking_number}")

        # Check authentication requirement
        self.authenticate()

        # Build request parameters based on provider type
        headers = {
            "User-Agent": "ShipTrack-AI/1.0",
            "Content-Type": "application/json"
        }
        
        if self.provider_name == 'trackingmore':
            endpoint = self.api_url or "https://api.trackingmore.com/v4/trackings/realtime"
            headers["Tracking-Api-Key"] = self.api_key
            payload = {"tracking_number": tracking_number, "courier_code": "india-post"}
            method = "POST"
        elif self.provider_name == 'ship24':
            endpoint = self.api_url or "https://api.ship24.com/public/v1/trackers/track"
            headers["Authorization"] = f"Bearer {self.api_key}"
            payload = {"trackingNumber": tracking_number}
            method = "POST"
        else:
            # Default / indiapost_direct REST endpoint
            endpoint = self.api_url or "https://api.indiapost.gov.in/v1/tracking"
            headers["Authorization"] = f"Bearer {self.api_key}"
            payload = {"article_number": tracking_number}
            method = "GET"

        try:
            if method == "POST":
                res = requests.post(endpoint, headers=headers, json=payload, timeout=12)
            else:
                res = requests.get(endpoint, headers=headers, params=payload, timeout=12)
                
            return self.parse_response(tracking_number, res.status_code, res.json() if res.content else {})
            
        except requests.exceptions.Timeout:
            logger.error(f"Provider timeout connecting to {self.provider_name} for {tracking_number}")
            raise TimeoutError(f"Tracking provider timed out for {tracking_number}")
        except requests.exceptions.RequestException as e:
            logger.error(f"Provider connection error: {e}")
            raise ConnectionError(f"Failed to connect to tracking provider: {e}")

    def parse_response(self, tracking_number: str, status_code: int, response_json: Dict[str, Any]) -> Dict[str, Any]:
        """Translates HTTP status codes and parses raw JSON response."""
        if status_code in (401, 403):
            raise PermissionError("Provider authentication failed. Check TRACKING_API_KEY.")
        if status_code == 404:
            raise KeyError(f"Tracking number {tracking_number} not found by provider.")
        if status_code == 429:
            raise RuntimeError("Provider rate limit exceeded. Please retry later.")
        if status_code >= 500:
            raise ConnectionError(f"Tracking provider service unavailable (HTTP {status_code}).")

        if not response_json or not isinstance(response_json, dict):
            raise ValueError("Malformed or empty response received from tracking provider.")

        return CarrierNormalizer.normalize_response(tracking_number, response_json)

    def get_tracking_history(self, tracking_number: str) -> List[Dict[str, Any]]:
        data = self.track(tracking_number)
        return data.get('events', [])
