from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pandas as pd

from core.context.market_context import MarketContext
from core.signal.signal import StrategySignal
from core.strategies.base import BaseStrategy
from pipeline.context_builder import build_context
from pipeline.indicator_pipeline import IndicatorPipeline


@dataclass
class StepResult:
    context: MarketContext
    signal: StrategySignal
    execution: dict[str, Any]


class TradingPipeline:
    """
    Mode-agnostic pipeline core: bars → indicators → context → signal.

    This class is shared between BacktestRunner and LiveRunner. It has no
    knowledge of how bars are sourced or how signals are executed — those
    responsibilities belong to the mode-specific runners.
    """

    def __init__(
        self,
        strategy: BaseStrategy,
        indicator_pipeline: IndicatorPipeline,
    ) -> None:
        self.strategy = strategy
        self.indicator_pipeline = indicator_pipeline

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
