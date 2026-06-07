from __future__ import annotations

from typing import Any

import pandas as pd

from core.execution.base import BaseExecutor
from core.signal.signal import StrategySignal


class SimulatedBroker(BaseExecutor):
    """
    Records target positions without placing real orders.

    Implements BaseExecutor so it can be dropped into any pipeline step.
    Also exposes position_series() for equity-curve computation after the
    backtest loop completes.
    """

    def __init__(self) -> None:
        self._positions: list[tuple[pd.Timestamp, float]] = []

    def handle(self, signal: StrategySignal) -> dict[str, Any]:
        self._positions.append((signal.timestamp, signal.target_position))
        return {
            "status": "recorded",
            "timestamp": signal.timestamp.isoformat(),
            "direction": signal.direction,
            "target_position": signal.target_position,
        }

    # kept for backward compat with BacktestRunner equity computation
    def on_signal(self, signal: StrategySignal) -> None:
        self._positions.append((signal.timestamp, signal.target_position))

    def position_series(self, index: pd.Index) -> pd.Series:
        series = pd.Series(
            {ts: pos for ts, pos in self._positions}, dtype=float
        )
        return series.reindex(index).ffill().fillna(0.0)
