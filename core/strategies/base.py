from __future__ import annotations

from abc import ABC, abstractmethod

from core.context.market_bundle import MarketBundle
from core.signal.signal import StrategySignal


class BaseStrategy(ABC):
    def __init__(self, strategy_name: str) -> None:
        self.strategy_name = strategy_name

    @abstractmethod
    def evaluate(self, bundle: MarketBundle) -> StrategySignal:
        """
        Consume a MarketBundle and return a StrategySignal.

        Single-asset strategies use bundle.primary.
        Multi-asset / multi-timeframe strategies look up additional contexts
        via bundle.get(symbol, timeframe).
        """
        raise NotImplementedError
