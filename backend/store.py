import re
from datetime import datetime, timezone

from .models import Shipment, TrackingEvent

TRACKING_PATTERN = re.compile(r"^[A-Z]{2}[0-9]{9}IN$")


class ShipmentStore:
    def __init__(self) -> None:
        self._shipments: dict[str, Shipment] = {}

    def list_shipments(self) -> list[Shipment]:
        return list(self._shipments.values())

    def get_shipment(self, shipment_id: str) -> Shipment | None:
        return self._shipments.get(shipment_id)

    def add_shipment(self, payload: dict) -> Shipment:
        tracking_number = payload.get("tracking_number", "").strip().upper()
        if not TRACKING_PATTERN.fullmatch(tracking_number):
            raise ValueError("tracking_number must match [A-Z]{2}[0-9]{9}IN")

        shipment = Shipment(
            tracking_number=tracking_number,
            description=payload.get("description", "").strip(),
            category=payload.get("category", "general").strip() or "general",
            carrier=payload.get("carrier", "India Post").strip() or "India Post",
            notes=payload.get("notes", "").strip(),
            priority=payload.get("priority", "medium").strip() or "medium",
            expected_delivery=payload.get("expected_delivery", "").strip(),
        )
        shipment.tracking_history.append(
            TrackingEvent(
                status="Booked",
                location="Origin Facility",
                description="Shipment created in ShipTrack AI scaffold",
            )
        )
        self._shipments[shipment.id] = shipment
        return shipment

    def refresh_shipment(self, shipment_id: str) -> Shipment | None:
        shipment = self.get_shipment(shipment_id)
        if shipment is None:
            return None

        shipment.status = "in_transit"
        shipment.location = "Transit Hub"
        shipment.updated_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
        shipment.tracking_history.append(
            TrackingEvent(
                status="Transit",
                location="Transit Hub",
                description="Manual refresh scaffold event",
            )
        )
        return shipment


store = ShipmentStore()
