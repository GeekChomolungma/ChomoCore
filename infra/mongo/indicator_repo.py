from __future__ import annotations

from typing import Any

import pandas as pd
from pymongo.database import Database


class IndicatorRepository:
    """
    Persistence for computed indicator values.

    Intended schema (one document per bar per indicator set):
        {
            "symbol":    str,
            "timeframe": str,
            "starttime": int,   # ms UTC epoch, same key as kline docs
            "indicators": {
                "rsi_14":          float,
                "st_value":        float,
                "st_direction":    int,
                "reversal_upper":  float,
                "reversal_lower":  float,
                ...
            }
        }

    Collection naming: {SYMBOL}_{timeframe}_{Exchange}_indicators
    e.g.  BTCUSDT_1h_Binance_indicators

    Not yet implemented — placeholder for the persistence layer.
    Uncomment and fill in write() / load() once the schema is confirmed.
    """

    def __init__(self, db: Database, exchange: str = "Binance") -> None:
        self._db = db
        self._exchange = exchange

    def _collection_name(self, symbol: str, timeframe: str) -> str:
        return f"{symbol.upper()}_{timeframe}_{self._exchange}_indicators"

    def write(
        self,
        symbol: str,
        timeframe: str,
        enriched_bars: pd.DataFrame,
        indicator_cols: list[str],
    ) -> None:
        """
        Upsert indicator values for each bar in enriched_bars.

        enriched_bars must have a DatetimeIndex (UTC) and contain all
        columns listed in indicator_cols.
        """
        raise NotImplementedError(
            "IndicatorRepository.write() is a placeholder. "
            "Implement once the persistence schema is confirmed."
        )

    def load(
        self,
        symbol: str,
        timeframe: str,
        start: str | None = None,
        end: str | None = None,
    ) -> pd.DataFrame:
        raise NotImplementedError(
            "IndicatorRepository.load() is a placeholder."
        )
