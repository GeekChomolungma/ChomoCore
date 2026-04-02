from __future__ import annotations

import pandas as pd

from quant_core.signal.signal import StrategySignal


class SimulatedBroker:
    def __init__(self) -> None:
        self._positions: list[tuple[pd.Timestamp, float]] = []

    def on_signal(self, signal: StrategySignal) -> None:
        self._positions.append((signal.timestamp, signal.target_position))

    def position_series(self, index: pd.Index) -> pd.Series:
        series = pd.Series({timestamp: position for timestamp, position in self._positions}, dtype=float)
        return series.reindex(index).ffill().fillna(0.0)
