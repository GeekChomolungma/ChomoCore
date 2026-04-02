from __future__ import annotations

from dataclasses import asdict

from quant_core.strategies.base import BaseStrategy
from quant_live.data.base import LiveDataSource
from quant_live.state.position_state import PositionState
from quant_live.transport.http_executor import HttpSignalExecutor


class LiveTradingEngine:
    def __init__(
        self,
        strategy: BaseStrategy,
        datasource: LiveDataSource,
        executor: HttpSignalExecutor,
        state: PositionState | None = None,
    ):
        self.strategy = strategy
        self.datasource = datasource
        self.executor = executor
        self.state = state or PositionState()

    def step(self, symbol: str, timeframe: str) -> dict:
        context = self.datasource.get_latest_context(symbol=symbol, timeframe=timeframe)
        signal = self.strategy.evaluate(context)
        self.state.update(signal)
        payload = asdict(signal)
        payload["timestamp"] = signal.timestamp.isoformat()
        execution_response = self.executor.send_signal(payload)
        return {
            "signal": payload,
            "execution_response": execution_response,
            "latest_position": self.state.get(symbol),
        }
