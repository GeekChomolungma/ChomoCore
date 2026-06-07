from __future__ import annotations

from dataclasses import asdict
from typing import Any

from core.execution.base import BaseExecutor
from core.strategies.base import BaseStrategy
from live.data.base import LiveDataSource
from live.state.position_state import PositionState
from pipeline.indicator_pipeline import IndicatorPipeline
from pipeline.runner import TradingPipeline


class LiveRunner:
    """
    Drives TradingPipeline in live mode.

    Each call to step() fetches the latest bar window from the data source,
    runs the full pipeline, sends the signal through the executor, and updates
    in-memory position state.

    In practice, step() is called once per closed bar (triggered externally,
    e.g. by a scheduler or a Redis pub/sub event on bar close).
    """

    def __init__(
        self,
        strategy: BaseStrategy,
        indicator_pipeline: IndicatorPipeline,
        datasource: LiveDataSource,
        executor: BaseExecutor,
        state: PositionState | None = None,
    ) -> None:
        self._pipeline = TradingPipeline(strategy, indicator_pipeline)
        self.datasource = datasource
        self.executor = executor
        self.state = state or PositionState()

    def step(self, symbol: str, timeframe: str) -> dict[str, Any]:
        raw_context = self.datasource.get_latest_context(symbol=symbol, timeframe=timeframe)
        context, signal = self._pipeline.step(
            symbol=symbol,
            timeframe=timeframe,
            bars=raw_context.bars,
            market_meta=raw_context.market_meta,
        )
        self.state.update(signal)
        execution = self.executor.handle(signal)

        return {
            "signal": {**asdict(signal), "timestamp": signal.timestamp.isoformat()},
            "execution": execution,
            "position": self.state.get(symbol),
        }
