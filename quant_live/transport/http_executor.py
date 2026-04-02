from __future__ import annotations

from typing import Any

import requests


class HttpSignalExecutor:
    def __init__(self, endpoint: str, timeout: float = 3.0, dry_run: bool = True):
        self.endpoint = endpoint
        self.timeout = timeout
        self.dry_run = dry_run

    def send_signal(self, payload: dict[str, Any]) -> dict[str, Any]:
        if self.dry_run:
            return {"status": "dry_run", "endpoint": self.endpoint, "payload": payload}

        response = requests.post(self.endpoint, json=payload, timeout=self.timeout)
        response.raise_for_status()
        return {"status": "sent", "code": response.status_code, "body": response.json()}
