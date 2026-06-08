from __future__ import annotations

from typing import Any

import pandas as pd

from core.context.market_context import MarketContext
from core.signal.signal import StrategySignal
from core.strategies.base import BaseStrategy
from core.strategies.registry import StrategyRegistry
from pipeline.context_builder import build_context
from pipeline.indicator_pipeline import IndicatorPipeline


class TradingPipeline:
    """
    Mode-agnostic pipeline core: bars → indicators → context → signal.

    Construct via from_config() to wire strategy and indicators from a
    config dict. The engine only needs to deal with this single object.
    """

    def __init__(
        self,
        strategy: BaseStrategy,
        indicator_pipeline: IndicatorPipeline,
    ) -> None:
        self.strategy = strategy
        self.indicator_pipeline = indicator_pipeline

    @classmethod
    def from_config(cls, config: dict[str, Any]) -> TradingPipeline:
        strategy = StrategyRegistry.create(
            config["strategy"]["name"],
            **config["strategy"].get("params", {}),
        )
        indicator_pipeline = IndicatorPipeline.from_config(
            config.get("indicators", [])
        )
        return cls(strategy, indicator_pipeline)

    def step(
        self,
        symbol: str,
        timeframe: str,
        bars: pd.DataFrame,
        market_meta: dict[str, Any] | None = None,
    ) -> tuple[MarketContext, StrategySignal]:
        """
        Run one pipeline step for a given bar window.

        Returns (context, signal). The caller is responsible for passing the
        signal to whichever executor is appropriate for the current mode.
        """
        enriched, indicator_cols = self.indicator_pipeline.apply(bars)
        context = build_context(
            symbol=symbol,
            timeframe=timeframe,
            enriched_bars=enriched,
            indicator_cols=indicator_cols,
            market_meta=market_meta,
        )
        signal = self.strategy.evaluate(context)
        return context, signal
