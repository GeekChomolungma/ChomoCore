from __future__ import annotations

from abc import ABC, abstractmethod

from quant_core.context.market_context import MarketContext


class LiveDataSource(ABC):
    @abstractmethod
    def get_latest_context(self, symbol: str, timeframe: str) -> MarketContext:
        raise NotImplementedError
