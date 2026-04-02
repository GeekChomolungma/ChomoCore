from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

import pandas as pd


SignalDirection = Literal["long", "short", "flat"]


@dataclass(slots=True)
class StrategySignal:
    symbol: str
    timeframe: str
    timestamp: pd.Timestamp
    strategy_name: str
    direction: SignalDirection
    target_position: float
    score: float | None = None
    confidence: float | None = None
    meta: dict[str, Any] | None = None

    def __post_init__(self) -> None:
        self.timestamp = pd.Timestamp(self.timestamp)

        if self.direction not in {"long", "short", "flat"}:
            raise ValueError(f"Unsupported direction: {self.direction}")

        if not -1.0 <= self.target_position <= 1.0:
            raise ValueError("target_position must be within [-1.0, 1.0]")

        if self.direction == "flat" and self.target_position != 0.0:
            raise ValueError("flat signals must have target_position == 0.0")
