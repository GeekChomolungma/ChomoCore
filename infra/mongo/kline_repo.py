from __future__ import annotations

from typing import Any

import pandas as pd
from pymongo.database import Database


# Fields in the Binance kline document that map to optional bar columns.
_OPTIONAL_FIELD_MAP: dict[str, str] = {
    "quotevolume": "quote_volume",
    "tradenum": "trade_count",
    "activebuyvolume": "taker_buy_volume",
    "isfinal": "is_closed",
}


def _collection_name(symbol: str, timeframe: str, exchange: str) -> str:
    """
    Construct the MongoDB collection name from parts.

    Convention (from screenshot): {SYMBOL}_{timeframe}_{Exchange}
    e.g.  BTCUSDT_1h_Binance
    """
    return f"{symbol.upper()}_{timeframe}_{exchange}"


def _doc_to_row(doc: dict[str, Any]) -> dict[str, Any]:
    """Convert one Mongo document to a flat dict of typed bar values."""
    row: dict[str, Any] = {
        "open": float(doc["open"]),
        "high": float(doc["high"]),
        "low": float(doc["low"]),
        "close": float(doc["close"]),
        "volume": float(doc["volume"]),
    }
    for mongo_field, bar_field in _OPTIONAL_FIELD_MAP.items():
        if mongo_field in doc:
            raw = doc[mongo_field]
            if bar_field == "is_closed":
                row[bar_field] = bool(raw)
            elif bar_field == "trade_count":
                row[bar_field] = int(raw)
            else:
                row[bar_field] = float(raw)
    return row


def _docs_to_dataframe(docs: list[dict[str, Any]]) -> pd.DataFrame:
    if not docs:
        return pd.DataFrame(
            columns=["open", "high", "low", "close", "volume"]
        )
    index = pd.DatetimeIndex(
        [pd.Timestamp(int(doc["starttime"]), unit="ms", tz="UTC") for doc in docs]
    )
    rows = [_doc_to_row(doc) for doc in docs]
    return pd.DataFrame(rows, index=index)


class KlineRepository:
    """
    Read/write access to the raw K-line collections in MongoDB.

    Collection naming follows the convention already established by the
    Binance data producer: {SYMBOL}_{timeframe}_{Exchange}.

    All timestamps are stored in the documents as millisecond UTC epochs
    (field: starttime). The DataFrame index returned is a UTC DatetimeIndex.
    """

    def __init__(self, db: Database, exchange: str = "Binance") -> None:
        self._db = db
        self._exchange = exchange

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    def load_bars(
        self,
        symbol: str,
        timeframe: str,
        start: str | pd.Timestamp | None = None,
        end: str | pd.Timestamp | None = None,
        limit: int | None = None,
    ) -> pd.DataFrame:
        """
        Load a time-sorted slice of closed K-lines.

        start / end are inclusive and accept any string parseable by pd.Timestamp.
        limit is applied after sorting; combine with end=None and a large limit
        to get the latest N bars.
        """
        col = self._db[_collection_name(symbol, timeframe, self._exchange)]
        query: dict[str, Any] = {}

        if start is not None or end is not None:
            ts_filter: dict[str, int] = {}
            if start is not None:
                ts_filter["$gte"] = int(pd.Timestamp(start).value // 1_000_000)
            if end is not None:
                ts_filter["$lte"] = int(pd.Timestamp(end).value // 1_000_000)
            query["starttime"] = ts_filter

        cursor = col.find(query, {"_id": 0}).sort("starttime", 1)
        if limit is not None:
            cursor = cursor.limit(limit)

        return _docs_to_dataframe(list(cursor))

    def load_latest(self, symbol: str, timeframe: str, n: int) -> pd.DataFrame:
        """
        Load the most recent n closed K-lines, returned in ascending time order.

        Used by live runners to prime the indicator warmup window.
        """
        col = self._db[_collection_name(symbol, timeframe, self._exchange)]
        # Sort descending to efficiently get the tail, then reverse.
        docs = list(col.find({}, {"_id": 0}).sort("starttime", -1).limit(n))
        docs.reverse()
        return _docs_to_dataframe(docs)

    def available_collections(self) -> list[str]:
        """Return all kline collection names in the database."""
        return [
            name
            for name in self._db.list_collection_names()
            if name != "system.indexes"
        ]
