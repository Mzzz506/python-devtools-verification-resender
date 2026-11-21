from __future__ import annotations

from dataclasses import dataclass

from .infrai_client import InfraiClient


@dataclass(frozen=True)
class VerificationRequest:
    message_id: str
    attempt: int


@dataclass(frozen=True)
class DeliveryReport:
    message_id: str
    state: str
    action: str


def resend_stuck_code(request: VerificationRequest, client: InfraiClient) -> DeliveryReport:
    if request.attempt < 1:
        raise ValueError("attempt must be positive")
    client.resend(request.message_id, f"verification-resend:{request.message_id}:{request.attempt}")
    result = client.events(request.message_id)
    data = result.get("data") or {}
    events = data.get("events") if isinstance(data, dict) else data
    latest = events[-1] if events else data
    state = latest.get("status", latest.get("state", "unknown"))
    action = "monitor" if state in {"queued", "sent", "delivered"} else "review"
    return DeliveryReport(request.message_id, state, action)
