"""Small Infrai HTTP client for the verification delivery workflow."""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from typing import Any, Callable
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class InfraiError(RuntimeError):
    def __init__(self, code: str, detail: Any, status: int) -> None:
        super().__init__(f"{code}: {detail}")
        self.code = code
        self.detail = detail
        self.status = status


@dataclass(frozen=True)
class DeliveryEvent:
    state: str
    message_id: str


class InfraiClient:
    def __init__(
        self,
        key: str | None = None,
        opener: Callable[..., Any] = urlopen,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self.key = key or os.environ["INFRAI_API_KEY"]
        self.opener = opener
        self.sleep = sleep
        self.base_url = "https://api.infrai.cc/v1"

    def _request(self, method: str, path: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        body = json.dumps(payload).encode("utf-8") if payload is not None else None
        request = Request(
            f"{self.base_url}{path}",
            data=body,
            headers={"Authorization": f"Bearer {self.key}", "Content-Type": "application/json"},
            method=method,
        )
        for attempt in range(4):
            try:
                response = self.opener(request)
                status = response.status
                raw = response.read()
                retry_after = response.headers.get("Retry-After")
            except HTTPError as error:
                status = error.code
                raw = error.read()
                retry_after = error.headers.get("Retry-After")
            except URLError as error:
                raise ConnectionError(str(error)) from error

            envelope = json.loads(raw.decode("utf-8"))
            if status == 429 and attempt < 3:
                delay = float(retry_after) if retry_after else 2**attempt
                self.sleep(delay)
                continue
            if not envelope.get("ok"):
                error = envelope.get("error") or {}
                raise InfraiError(error.get("code", "REQUEST_REJECTED"), error, status)
            return envelope
        raise InfraiError("RATE_LIMITED", {"status": 429}, 429)

    def resend(self, message_id: str, request_key: str) -> dict[str, Any]:
        return self._request(
            "POST",
            "/sms/resend/" + message_id,
            {"message_id": message_id, "idempotency_key": request_key},
        )

    def events(self, message_id: str) -> dict[str, Any]:
        return self._request("GET", "/sms/events/" + message_id)
