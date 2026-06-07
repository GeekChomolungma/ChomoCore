from __future__ import annotations

from dataclasses import dataclass

from core.context.market_context import MarketContext
from core.indicators.ta_utils import sma
from core.signal.signal import StrategySignal
from core.strategies.base import BaseStrategy
from core.strategies.registry import StrategyRegistry


@dataclass(slots=True)
class MACrossParams:
    fast_window: int = 10
    slow_window: int = 30
    max_position: float = 1.0


@StrategyRegistry.register("ma_cross")
class MovingAverageCrossStrategy(BaseStrategy):
    def __init__(
        self,
        fast_window: int = 10,
        slow_window: int = 30,
        max_position: float = 1.0,
    ) -> None:
        super().__init__("ma_cross")
        if fast_window >= slow_window:
            raise ValueError("fast_window must be smaller than slow_window")
        self.params = MACrossParams(fast_window, slow_window, max_position)

    def evaluate(self, context: MarketContext) -> StrategySignal:
        closes = context.bars["close"]
        fast_value = float(sma(closes, self.params.fast_window).iloc[-1])
        slow_value = float(sma(closes, self.params.slow_window).iloc[-1])
        spread = (fast_value - slow_value) / max(abs(slow_value), 1e-12)

        if fast_value > slow_value:
            direction, target_position = "long", self.params.max_position
        elif fast_value < slow_value:
            direction, target_position = "short", -self.params.max_position
        else:
            direction, target_position = "flat", 0.0

        return StrategySignal(
            symbol=context.symbol,
            timeframe=context.timeframe,
            timestamp=context.timestamp,
            strategy_name=self.strategy_name,
            direction=direction,
            target_position=target_position,
            score=spread,
            confidence=min(abs(spread) * 10.0, 1.0),
            meta={
                "fast_window": self.params.fast_window,
                "slow_window": self.params.slow_window,
                "fast_ma": fast_value,
                "slow_ma": slow_value,
            },
        )
