from __future__ import annotations

from dataclasses import dataclass

from quant_core.context.market_context import MarketContext
from quant_core.signal.signal import StrategySignal
from quant_core.strategies.base import BaseStrategy
from quant_core.strategies.registry import StrategyRegistry
from quant_core.features.ta import sma


@dataclass(slots=True)
class MovingAverageCrossParams:
    fast_window: int = 10
    slow_window: int = 30
    max_position: float = 1.0


@StrategyRegistry.register("ma_cross")
class MovingAverageCrossStrategy(BaseStrategy):
    def __init__(self, fast_window: int = 10, slow_window: int = 30, max_position: float = 1.0):
        super().__init__("ma_cross")
        if fast_window >= slow_window:
            raise ValueError("fast_window must be smaller than slow_window")
        self.params = MovingAverageCrossParams(fast_window, slow_window, max_position)

    def evaluate(self, context: MarketContext) -> StrategySignal:
        closes = context.bars["close"]
        fast = sma(closes, self.params.fast_window)
        slow = sma(closes, self.params.slow_window)

        fast_value = float(fast.iloc[-1])
        slow_value = float(slow.iloc[-1])
        spread = (fast_value - slow_value) / max(abs(slow_value), 1e-12)

        if fast_value > slow_value:
            direction = "long"
            target_position = self.params.max_position
        elif fast_value < slow_value:
            direction = "short"
            target_position = -self.params.max_position
        else:
            direction = "flat"
            target_position = 0.0

        confidence = min(abs(spread) * 10.0, 1.0)
        return StrategySignal(
            symbol=context.symbol,
            timeframe=context.timeframe,
            timestamp=context.timestamp,
            strategy_name=self.strategy_name,
            direction=direction,
            target_position=target_position,
            score=spread,
            confidence=confidence,
            meta={
                "fast_window": self.params.fast_window,
                "slow_window": self.params.slow_window,
                "fast_ma": fast_value,
                "slow_ma": slow_value,
            },
        )
