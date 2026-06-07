from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from core.signal.signal import StrategySignal


class BaseExecutor(ABC):
    """
    Contract for all execution backends.

    In live mode this sends signals to a downstream system (e.g. HTTP).
    In backtest mode this records signals for post-hoc analysis.
    Both return a dict summarising what happened so the caller can log uniformly.
    """

    @abstractmethod
    def handle(self, signal: StrategySignal) -> dict[str, Any]:
        raise NotImplementedError
