from __future__ import annotations

from dataclasses import dataclass

from core.context.market_bundle import MarketBundle
from core.indicators.rsi import add_rsi
from core.signal.signal import StrategySignal
from core.strategies.base import BaseStrategy
from core.strategies.registry import StrategyRegistry


@dataclass(slots=True)
class RSIParams:
    window: int = 14
    oversold: float = 30.0
    overbought: float = 70.0
    max_position: float = 1.0


@StrategyRegistry.register("rsi")
class RSIStrategy(BaseStrategy):
    def __init__(
        self,
        window: int = 14,
        oversold: float = 30.0,
        overbought: float = 70.0,
        max_position: float = 1.0,
    ) -> None:
        super().__init__("rsi")
        self.params = RSIParams(window, oversold, overbought, max_position)

    def evaluate(self, bundle: MarketBundle) -> StrategySignal:
        context = bundle.primary
        col = f"rsi_{self.params.window}"

        if context.features and col in context.features:
            latest_rsi = float(context.features[col])
        else:
            enriched = add_rsi(context.bars, length=self.params.window)
            latest_rsi = float(enriched[col].iloc[-1])

        if latest_rsi <= self.params.oversold:
            direction = "long"
            target_position = self.params.max_position
            score = (self.params.oversold - latest_rsi) / max(self.params.oversold, 1e-12)
        elif latest_rsi >= self.params.overbought:
            direction = "short"
            target_position = -self.params.max_position
            score = (latest_rsi - self.params.overbought) / max(100 - self.params.overbought, 1e-12)
        else:
            direction = "flat"
            target_position = 0.0
            score = 0.0

        return StrategySignal(
            symbol=context.symbol,
            timeframe=context.timeframe,
            timestamp=context.timestamp,
            strategy_name=self.strategy_name,
            direction=direction,
            target_position=target_position,
            score=score,
            confidence=min(abs(score), 1.0),
            meta={"rsi": latest_rsi, "window": self.params.window},
        )
