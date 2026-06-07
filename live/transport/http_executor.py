from __future__ import annotations

from typing import Any

import requests

from core.execution.base import BaseExecutor
from core.signal.signal import StrategySignal


class HttpSignalExecutor(BaseExecutor):
    """
    Sends a StrategySignal as a JSON POST to a downstream execution endpoint.

    dry_run=True (default) returns a mock response without making any HTTP
    call — safe for development and backtest validation.
    """

    def __init__(
        self,
        endpoint: str,
        timeout: float = 3.0,
        dry_run: bool = True,
    ) -> None:
        self.endpoint = endpoint
        self.timeout = timeout
        self.dry_run = dry_run

    def handle(self, signal: StrategySignal) -> dict[str, Any]:
        payload = {
            "symbol": signal.symbol,
            "timeframe": signal.timeframe,
            "timestamp": signal.timestamp.isoformat(),
            "strategy_name": signal.strategy_name,
            "direction": signal.direction,
            "target_position": signal.target_position,
            "score": signal.score,
            "confidence": signal.confidence,
            "meta": signal.meta,
        }

        if self.dry_run:
            return {"status": "dry_run", "endpoint": self.endpoint, "payload": payload}

        response = requests.post(self.endpoint, json=payload, timeout=self.timeout)
        response.raise_for_status()
        return {"status": "sent", "code": response.status_code, "body": response.json()}
