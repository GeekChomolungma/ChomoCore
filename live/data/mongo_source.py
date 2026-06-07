from __future__ import annotations

import pandas as pd

from backtest.data.base import HistoricalDataSource


class MongoHistoricalDataSource(HistoricalDataSource):
    """
    Placeholder for a MongoDB-backed historical bar loader.

    Replace the body of load_bars() with real pymongo logic once the
    collection schema and connection details are confirmed. The expected
    document format will be provided separately.

    Assumed document shape (to be confirmed):
        {
            "symbol":     str,
            "timeframe":  str,
            "open_time":  int (ms epoch),
            "open":       float,
            "high":       float,
            "low":        float,
            "close":      float,
            "volume":     float,
            ...
        }
    """

    def __init__(self, uri: str, db: str, collection: str) -> None:
        self.uri = uri
        self.db = db
        self.collection = collection

    def load_bars(
        self,
        symbol: str,
        timeframe: str,
        start: str | None = None,
        end: str | None = None,
    ) -> pd.DataFrame:
        raise NotImplementedError(
            "MongoHistoricalDataSource.load_bars() is a placeholder. "
            "Implement once the collection schema is confirmed."
        )
