from __future__ import annotations

from dataclasses import asdict
from typing import Any

from pymongo.database import Database

from core.signal.signal import StrategySignal


class SignalRepository:
    """
    Persistence for strategy signals.

    Intended schema (one document per signal):
        {
            "symbol":          str,
            "timeframe":       str,
            "timestamp":       int,   # ms UTC epoch
            "strategy_name":   str,
            "direction":       str,   # "long" | "short" | "flat"
            "target_position": float,
            "score":           float | null,
            "confidence":      float | null,
            "meta":            dict | null,
            "mode":            str,   # "live" | "backtest"
        }

    Collection naming: signals_{strategy_name}
    e.g.  signals_rsi,  signals_ma_cross

    Not yet implemented — placeholder for the persistence layer.
    """

    def __init__(self, db: Database) -> None:
        self._db = db

    def _collection_name(self, strategy_name: str) -> str:
        return f"signals_{strategy_name}"

    def write(self, signal: StrategySignal, mode: str) -> None:
        """Persist one signal document."""
        raise NotImplementedError(
            "SignalRepository.write() is a placeholder. "
            "Implement once the collection schema is confirmed."
        )

    def load(
        self,
        strategy_name: str,
        symbol: str | None = None,
        start: str | None = None,
        end: str | None = None,
    ) -> list[dict[str, Any]]:
        raise NotImplementedError(
            "SignalRepository.load() is a placeholder."
        )
