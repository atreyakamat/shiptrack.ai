import os

import requests
import streamlit as st

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:5000")
API_PREFIX = f"{API_BASE_URL}/api/v1"

st.set_page_config(page_title="ShipTrack AI", page_icon="📦", layout="wide")
st.title("ShipTrack AI")
st.caption("Basic PRD-aligned scaffold")


def fetch_shipments() -> tuple[list[dict], str]:
    try:
        response = requests.get(f"{API_PREFIX}/shipments", timeout=5)
        response.raise_for_status()
        return response.json(), ""
    except requests.RequestException as error:
        return [], str(error)


with st.sidebar:
    st.subheader("Navigation")
    view = st.radio("View", ["Dashboard", "Add Shipment", "Shipments"])

if view == "Dashboard":
    st.subheader("Dashboard")
    shipments, error = fetch_shipments()
    if error:
        st.warning(f"Backend unavailable: {error}")
    total = len(shipments)
    delivered = sum(1 for item in shipments if item.get("status") == "delivered")
    in_transit = sum(1 for item in shipments if item.get("status") == "in_transit")
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Shipments", total)
    col2.metric("In Transit", in_transit)
    col3.metric("Delivered", delivered)

if view == "Add Shipment":
    st.subheader("Add Shipment")
    with st.form("add_shipment_form", clear_on_submit=True):
        tracking_number = st.text_input("Tracking Number (e.g., EM740043207IN)")
        description = st.text_input("Description")
        category = st.text_input("Category", value="general")
        priority = st.selectbox("Priority", options=["low", "medium", "high"], index=1)
        submitted = st.form_submit_button("Create Shipment")

        if submitted:
            payload = {
                "tracking_number": tracking_number.strip().upper(),
                "description": description,
                "category": category,
                "priority": priority,
                "carrier": "India Post",
            }
            try:
                response = requests.post(f"{API_PREFIX}/shipments", json=payload, timeout=5)
                if response.status_code == 201:
                    st.success("Shipment created")
                else:
                    st.error(response.json().get("error", "Failed to create shipment"))
            except requests.RequestException as error:
                st.error(f"Backend unavailable: {error}")

if view == "Shipments":
    st.subheader("Shipments")
    shipments, error = fetch_shipments()
    if error:
        st.warning(f"Backend unavailable: {error}")
    elif not shipments:
        st.info("No shipments yet")
    else:
        st.dataframe(
            [
                {
                    "id": item["id"],
                    "tracking_number": item["tracking_number"],
                    "status": item["status"],
                    "location": item.get("location", ""),
                    "updated_at": item["updated_at"],
                }
                for item in shipments
            ],
            use_container_width=True,
        )
