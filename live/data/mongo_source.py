from __future__ import annotations

import pandas as pd

from core.context.market_context import MarketContext
from infra.mongo.kline_repo import KlineRepository
from live.data.base import LiveDataSource


class MongoLiveDataSource(LiveDataSource):
    """
    LiveDataSource backed by KlineRepository.

    Fetches the latest `window_size` closed K-lines from MongoDB to serve
    as the indicator warmup window. This is the historical half of the live
    data picture; the in-progress (open) bar will be merged from Redis once
    that adapter is implemented.

    window_size should be at least max(indicator_lookback) + 1 so that all
    indicators have enough history to produce non-NaN values on the last bar.
    """

    def __init__(self, repo: KlineRepository, window_size: int = 200) -> None:
        self._repo = repo
        self._window_size = window_size

    def get_latest_context(self, symbol: str, timeframe: str) -> MarketContext:
        bars = self._repo.load_latest(
            symbol=symbol,
            timeframe=timeframe,
            n=self._window_size,
        )
        if bars.empty:
            raise RuntimeError(
                f"No kline data found for {symbol} {timeframe}. "
                "Check that the MongoDB collection exists and contains data."
            )
        return MarketContext(
            symbol=symbol,
            timeframe=timeframe,
            timestamp=pd.Timestamp(bars.index[-1]),
            bars=bars,
            market_meta={"source": "mongo", "window_size": self._window_size},
        )
