import requests
import streamlit as st
import logging

logger = logging.getLogger(__name__)

class ShipTrackAPI:
    def __init__(self, base_url='http://localhost:5000/api', token=None):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({'Content-Type': 'application/json'})
        if token:
            self.set_token(token)

    def set_token(self, token):
        self.session.headers.update({'Authorization': f'Bearer {token}'})
        
    def login(self, email, password):
        try:
            res = self.session.post(f"{self.base_url}/auth/login", json={"email": email, "password": password})
            data = self._handle_response(res)
            if data and 'token' in data:
                self.set_token(data['token'])
                return data['token']
            return None
        except requests.exceptions.RequestException as e:
            st.error(f"Login failed: {e}")
            return None

    def register(self, email, password):
        try:
            res = self.session.post(f"{self.base_url}/auth/register", json={"email": email, "password": password})
            data = self._handle_response(res)
            if data and 'token' in data:
                self.set_token(data['token'])
                return data['token']
            return None
        except requests.exceptions.RequestException as e:
            st.error(f"Registration failed: {e}")
            return None

    def _handle_response(self, response):
        try:
            response.raise_for_status()
            json_data = response.json()
            if isinstance(json_data, dict) and 'success' in json_data:
                if json_data['success']:
                    return json_data.get('data')
                else:
                    msg = json_data.get('error', {}).get('message', 'Unknown Error')
                    st.error(f"{msg}")
                    return None
            return json_data
        except requests.exceptions.HTTPError as e:
            code = response.status_code
            try:
                err_data = response.json()
                msg = err_data.get('error', {}).get('message')
                if msg:
                    st.error(msg)
                    return None
            except Exception:
                pass
                
            if code in (400, 422):
                st.error("Please check the shipment details.")
            elif code == 401:
                st.error("Your session has expired. Please log in again.")
            elif code == 403:
                st.error("You don't have permission to perform this action.")
            elif code == 404:
                st.error("Shipment not found.")
            elif code == 409:
                st.error("This tracking number is already in your shipments.")
            elif code == 429:
                st.error("The tracking provider is temporarily rate-limiting requests. Please try again later.")
            elif code == 503:
                st.error("The tracking provider is currently unavailable.")
            elif code >= 500:
                st.error("ShipTrack AI encountered an unexpected internal error.")
            else:
                st.error("An unexpected server error occurred.")
            return None
        except requests.exceptions.ConnectionError:
            st.error("ShipTrack AI could not connect to the server.")
            return None
        except requests.exceptions.Timeout:
            st.error("The request timed out. Please try again.")
            return None
        except Exception:
            st.error("An unexpected error occurred.")
            return None

    def health_check(self) -> dict:
        try:
            res = self.session.get(f"{self.base_url}/health", timeout=5)
            return self._handle_response(res) or {}
        except requests.exceptions.RequestException:
            return {}

    def get_shipments(self, search=None, status=None, carrier=None, category=None, priority=None) -> list:
        params = {}
        if search: params['search'] = search
        if status: params['status'] = status
        if carrier: params['carrier'] = carrier
        if category: params['category'] = category
        if priority: params['priority'] = priority
        
        try:
            res = self.session.get(f"{self.base_url}/shipments", params=params)
            data = self._handle_response(res)
            return data if data else []
        except requests.exceptions.RequestException as e:
            st.error(f"Failed to fetch shipments: {e}")
            return []

    def get_shipment(self, id: str) -> dict:
        try:
            res = self.session.get(f"{self.base_url}/shipments/{id}")
            return self._handle_response(res)
        except requests.exceptions.RequestException as e:
            st.error(f"Failed to fetch shipment {id}: {e}")
            return None

    def create_shipment(self, data: dict) -> dict:
        try:
            res = self.session.post(f"{self.base_url}/shipments", json=data)
            return self._handle_response(res)
        except requests.exceptions.RequestException as e:
            st.error(f"Failed to create shipment: {e}")
            return None

    def update_shipment(self, id: str, data: dict) -> dict:
        try:
            res = self.session.put(f"{self.base_url}/shipments/{id}", json=data)
            return self._handle_response(res)
        except requests.exceptions.RequestException as e:
            st.error(f"Failed to update shipment {id}: {e}")
            return None

    def delete_shipment(self, id: str) -> bool:
        try:
            res = self.session.delete(f"{self.base_url}/shipments/{id}")
            return res.status_code == 200
        except requests.exceptions.RequestException as e:
            st.error(f"Failed to delete shipment {id}: {e}")
            return False

    def archive_shipment(self, id: str) -> dict:
        try:
            res = self.session.post(f"{self.base_url}/shipments/{id}/archive")
            return self._handle_response(res)
        except requests.exceptions.RequestException as e:
            st.error(f"Failed to archive shipment {id}: {e}")
            return None

    def refresh_shipment(self, id: str) -> dict:
        try:
            res = self.session.post(f"{self.base_url}/shipments/{id}/refresh")
            return self._handle_response(res)
        except requests.exceptions.RequestException as e:
            st.error(f"Failed to refresh shipment {id}: {e}")
            return None

    def refresh_all(self) -> dict:
        try:
            res = self.session.post(f"{self.base_url}/shipments/refresh-all")
            return self._handle_response(res)
        except requests.exceptions.RequestException as e:
            st.error(f"Failed to refresh all shipments: {e}")
            return None

    def get_tracking_history(self, id: str) -> list:
        try:
            res = self.session.get(f"{self.base_url}/shipments/{id}/history")
            data = self._handle_response(res)
            return data if data else []
        except requests.exceptions.RequestException as e:
            st.error(f"Failed to fetch history for {id}: {e}")
            return []

    def upload_ocr(self, file) -> dict:
        try:
            files = {'file': (file.name, file.getvalue(), file.type)}
            # Do not use JSON content type for multipart/form-data
            headers = {k: v for k, v in self.session.headers.items() if k != 'Content-Type'}
            res = requests.post(f"{self.base_url}/ocr", files=files, headers=headers)
            return self._handle_response(res)
        except requests.exceptions.RequestException as e:
            st.error(f"OCR Upload failed: {e}")
            return None

    def confirm_ocr(self, data: dict) -> dict:
        try:
            res = self.session.post(f"{self.base_url}/ocr/confirm", json=data)
            return self._handle_response(res)
        except requests.exceptions.RequestException as e:
            st.error(f"Failed to confirm OCR data: {e}")
            return None

    def get_analytics(self) -> dict:
        try:
            res = self.session.get(f"{self.base_url}/analytics")
            return self._handle_response(res) or {}
        except requests.exceptions.RequestException as e:
            st.error(f"Failed to fetch analytics: {e}")
            return {}

    def get_ai_summary(self, shipment_id: str) -> dict:
        try:
            res = self.session.get(f"{self.base_url}/ai/{shipment_id}/summary")
            return self._handle_response(res)
        except requests.exceptions.RequestException as e:
            st.error(f"Failed to fetch AI summary: {e}")
            return None

    def generate_ai_summary(self, shipment_id: str) -> dict:
        try:
            res = self.session.post(f"{self.base_url}/ai/{shipment_id}/generate")
            return self._handle_response(res)
        except requests.exceptions.RequestException as e:
            st.error(f"Failed to generate AI summary: {e}")
            return None

    def get_insights(self) -> dict:
        try:
            res = self.session.get(f"{self.base_url}/ai/insights")
            return self._handle_response(res) or {}
        except requests.exceptions.RequestException as e:
            st.error(f"Failed to fetch AI insights: {e}")
            return {}

    def generate_insights(self) -> dict:
        try:
            res = self.session.post(f"{self.base_url}/ai/insights/generate")
            return self._handle_response(res)
        except requests.exceptions.RequestException as e:
            st.error(f"Failed to generate insights: {e}")
            return None

    def get_notifications(self) -> list:
        try:
            res = self.session.get(f"{self.base_url}/notifications")
            data = self._handle_response(res)
            return data if data else []
        except requests.exceptions.RequestException as e:
            st.error(f"Failed to fetch notifications: {e}")
            return []

    def mark_notification_read(self, id: str) -> dict:
        try:
            res = self.session.post(f"{self.base_url}/notifications/{id}/read")
            return self._handle_response(res)
        except requests.exceptions.RequestException as e:
            st.error(f"Failed to mark notification as read: {e}")
            return None

    def export_csv(self) -> bytes:
        try:
            res = self.session.get(f"{self.base_url}/analytics/export")
            res.raise_for_status()
            return res.content
        except requests.exceptions.RequestException as e:
            st.error(f"Failed to export CSV: {e}")
            return None
