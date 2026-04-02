from __future__ import annotations

import pandas as pd

from quant_core.context.market_context import MarketContext
from quant_live.data.base import LiveDataSource


class RedisLikeDataSource(LiveDataSource):
    """
    Placeholder for a Redis-backed market stream adapter.

    In production, replace the in-memory frame with logic that reads the latest
    rolling window from Redis and converts it into a clean MarketContext.
    """

    def __init__(self, bars: pd.DataFrame):
        self.bars = bars.sort_index()

    def get_latest_context(self, symbol: str, timeframe: str) -> MarketContext:
        return MarketContext(
            symbol=symbol,
            timeframe=timeframe,
            timestamp=pd.Timestamp(self.bars.index[-1]),
            bars=self.bars,
            market_meta={"source": "redis_like"},
        )
