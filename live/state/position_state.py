from __future__ import annotations

from core.signal.signal import StrategySignal


class PositionState:
    """In-memory position tracker. One entry per symbol."""

    def __init__(self) -> None:
        self._positions: dict[str, float] = {}

    def update(self, signal: StrategySignal) -> None:
        self._positions[signal.symbol] = signal.target_position

    def get(self, symbol: str) -> float:
        return self._positions.get(symbol, 0.0)

    def all(self) -> dict[str, float]:
        return dict(self._positions)
