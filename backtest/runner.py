from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pandas as pd

from backtest.broker.simulated import SimulatedBroker
from backtest.metrics.performance import compute_performance_metrics
from backtest.plots.equity import equity_summary
from core.strategies.base import BaseStrategy
from pipeline.indicator_pipeline import IndicatorPipeline
from pipeline.runner import TradingPipeline


@dataclass
class BacktestResult:
    positions: pd.Series
    equity_curve: pd.Series
    metrics: dict[str, float]
    signals: list[dict[str, Any]]


class BacktestRunner:
    """
    Drives TradingPipeline in a rolling-window replay loop.

    For each bar from warmup_bars onward, a growing window of bars is passed
    to TradingPipeline.step(). The SimulatedBroker records target positions and
    computes the equity curve once the loop completes.
    """

    def __init__(
        self,
        strategy: BaseStrategy,
        indicator_pipeline: IndicatorPipeline,
        warmup_bars: int = 50,
    ) -> None:
        self._pipeline = TradingPipeline(strategy, indicator_pipeline)
        self.warmup_bars = warmup_bars

    def run(self, symbol: str, timeframe: str, bars: pd.DataFrame) -> BacktestResult:
        broker = SimulatedBroker()
        signals: list[dict[str, Any]] = []

        for end_idx in range(self.warmup_bars, len(bars)):
            window = bars.iloc[: end_idx + 1]
            context, signal = self._pipeline.step(symbol, timeframe, window)
            broker.on_signal(signal)
            signals.append(
                {
                    "timestamp": signal.timestamp,
                    "direction": signal.direction,
                    "target_position": signal.target_position,
                    "score": signal.score,
                    "confidence": signal.confidence,
                }
            )

        active_index = bars.index[self.warmup_bars :]
        positions = broker.position_series(index=active_index)
        forward_returns = (
            bars["close"].pct_change().shift(-1).reindex(active_index).fillna(0.0)
        )
        strategy_returns = positions.shift(1).fillna(0.0) * forward_returns
        equity_curve = (1.0 + strategy_returns).cumprod()

        return BacktestResult(
            positions=positions,
            equity_curve=equity_curve,
            metrics=compute_performance_metrics(strategy_returns, equity_curve),
            signals=signals,
        )

    def report(self, result: BacktestResult) -> None:
        print("Backtest metrics:")
        for key, value in result.metrics.items():
            print(f"  {key}: {value:.6f}")
        print(equity_summary(result.equity_curve))
