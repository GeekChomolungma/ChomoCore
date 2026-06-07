from __future__ import annotations

import pandas as pd

from core.context.market_context import MarketContext
from live.data.base import LiveDataSource


class RedisLiveDataSource(LiveDataSource):
    """
    Placeholder for a Redis-backed live market stream adapter.

    In production, replace the in-memory bars with logic that reads the
    latest rolling window from Redis and converts it into a clean DataFrame.
    The rolling window must include enough history to warm up any indicators
    configured in the pipeline (e.g. at least max(indicator lookback) bars).

    Expected Redis key schema and serialisation format will be provided
    separately once the producer protocol is confirmed.
    """

    def __init__(self, bars: pd.DataFrame) -> None:
        self._bars = bars.sort_index()

    def get_latest_context(self, symbol: str, timeframe: str) -> MarketContext:
        return MarketContext(
            symbol=symbol,
            timeframe=timeframe,
            timestamp=pd.Timestamp(self._bars.index[-1]),
            bars=self._bars,
            market_meta={"source": "redis"},
        )
