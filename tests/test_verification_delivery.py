import json

from src.infrai_client import InfraiClient
from src.verification_delivery import VerificationRequest, resend_stuck_code


class Reply:
    def __init__(self, payload, status=200, headers=None):
        self.payload = json.dumps(payload).encode()
        self.status = status
        self.headers = headers or {}

    def read(self):
        return self.payload


def test_resend_reports_monitor_for_delivered_event():
    calls = []
    replies = iter([
        Reply({"ok": True, "data": {"message_id": "m-7"}}),
        Reply({"ok": True, "data": {"events": [{"status": "delivered"}]}}),
    ])

    def opener(request):
        calls.append((request.method, request.full_url, json.loads(request.data) if request.data else None))
        return next(replies)

    client = InfraiClient(key="test-key", opener=opener)
    report = resend_stuck_code(VerificationRequest("m-7", 2), client)

    assert report.state == "delivered"
    assert report.action == "monitor"
    assert calls[0][0] == "POST"
    assert calls[0][2] == {"message_id": "m-7", "idempotency_key": "verification-resend:m-7:2"}
    assert calls[1][0] == "GET"


def test_client_retries_non_ok_rate_limit_envelope():
    replies = iter([
        Reply({"ok": False, "error": {"code": "RATE_LIMITED"}}, status=429),
        Reply({"ok": True, "data": {"message_id": "m-8"}}),
    ])
    delays = []

    client = InfraiClient(key="test-key", opener=lambda request: next(replies), sleep=delays.append)

    result = client.resend("m-8", "request-key")

    assert result["ok"] is True
    assert delays == [1]
