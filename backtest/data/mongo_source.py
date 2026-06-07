from __future__ import annotations

import pandas as pd

from backtest.data.base import HistoricalDataSource
from infra.mongo.kline_repo import KlineRepository


class MongoHistoricalDataSource(HistoricalDataSource):
    """
    HistoricalDataSource backed by KlineRepository.

    Plugs into BacktestRunner as the bars provider. The bars DataFrame
    returned satisfies the MarketContext contract: OHLCV + optional columns,
    DatetimeIndex (UTC), ascending order.
    """

    def __init__(self, repo: KlineRepository) -> None:
        self._repo = repo

    def load_bars(
        self,
        symbol: str,
        timeframe: str,
        start: str | None = None,
        end: str | None = None,
    ) -> pd.DataFrame:
        return self._repo.load_bars(
            symbol=symbol,
            timeframe=timeframe,
            start=start,
            end=end,
        )
