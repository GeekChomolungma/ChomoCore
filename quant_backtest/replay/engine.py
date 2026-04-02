from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pandas as pd

from quant_backtest.broker.simulated import SimulatedBroker
from quant_backtest.metrics.performance import compute_performance_metrics
from quant_core.context.market_context import MarketContext
from quant_core.strategies.base import BaseStrategy


@dataclass(slots=True)
class BacktestResult:
    positions: pd.Series
    equity_curve: pd.Series
    metrics: dict[str, Any]
    signals: list[dict[str, Any]]


class BacktestEngine:
    def __init__(self, strategy: BaseStrategy, warmup_bars: int = 50):
        self.strategy = strategy
        self.warmup_bars = warmup_bars

    def run(self, symbol: str, timeframe: str, bars: pd.DataFrame) -> BacktestResult:
        broker = SimulatedBroker()
        signals: list[dict[str, Any]] = []

        for end_idx in range(self.warmup_bars, len(bars)):
            window = bars.iloc[: end_idx + 1]
            context = MarketContext(
                symbol=symbol,
                timeframe=timeframe,
                timestamp=pd.Timestamp(window.index[-1]),
                bars=window,
            )
            signal = self.strategy.evaluate(context)
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

        positions = broker.position_series(index=bars.index[self.warmup_bars :])
        forward_returns = bars["close"].pct_change().shift(-1).reindex(positions.index).fillna(0.0)
        strategy_returns = positions.shift(1).fillna(0.0) * forward_returns
        equity_curve = (1.0 + strategy_returns).cumprod()

        return BacktestResult(
            positions=positions,
            equity_curve=equity_curve,
            metrics=compute_performance_metrics(strategy_returns, equity_curve),
            signals=signals,
        )
