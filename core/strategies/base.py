from __future__ import annotations

from abc import ABC, abstractmethod

from core.context.market_context import MarketContext
from core.signal.signal import StrategySignal


class BaseStrategy(ABC):
    def __init__(self, strategy_name: str) -> None:
        self.strategy_name = strategy_name

    @abstractmethod
    def evaluate(self, context: MarketContext) -> StrategySignal:
        """
        Consume a standardized MarketContext and return a StrategySignal.
        Must be free of look-ahead bias: only context.bars rows up to
        context.timestamp may influence the output.
        """
        raise NotImplementedError
