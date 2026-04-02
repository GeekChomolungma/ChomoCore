from __future__ import annotations

from abc import ABC, abstractmethod

from quant_core.context.market_context import MarketContext
from quant_core.signal.signal import StrategySignal


class BaseStrategy(ABC):
    def __init__(self, strategy_name: str):
        self.strategy_name = strategy_name

    @abstractmethod
    def evaluate(self, context: MarketContext) -> StrategySignal:
        """
        Consume a standardized market context and return a standardized strategy signal.
        """
        raise NotImplementedError
