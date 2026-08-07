from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4


@dataclass
class TrackingEvent:
    status: str
    location: str
    description: str
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(timespec="seconds")
    )


@dataclass
class Shipment:
    tracking_number: str
    description: str = ""
    category: str = "general"
    carrier: str = "India Post"
    notes: str = ""
    priority: str = "medium"
    expected_delivery: str = ""
    id: str = field(default_factory=lambda: str(uuid4()))
    status: str = "created"
    location: str = ""
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(timespec="seconds")
    )
    updated_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(timespec="seconds")
    )
    tracking_history: list[TrackingEvent] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["tracking_history"] = [asdict(event) for event in self.tracking_history]
        return payload
