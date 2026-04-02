from __future__ import annotations

import numpy as np
import pandas as pd

from quant_backtest.data.base import HistoricalDataSource


class SyntheticOHLCVDataSource(HistoricalDataSource):
    def __init__(self, periods: int = 300, seed: int = 7):
        self.periods = periods
        self.seed = seed

    def load_bars(
        self,
        symbol: str,
        timeframe: str,
        start: str | None = None,
        end: str | None = None,
    ) -> pd.DataFrame:
        rng = np.random.default_rng(self.seed)
        index = pd.date_range(start=start or "2024-01-01", periods=self.periods, freq=_to_pandas_freq(timeframe))
        returns = rng.normal(loc=0.0005, scale=0.01, size=len(index))
        close = 100 * (1 + pd.Series(returns, index=index)).cumprod()
        open_ = close.shift(1).fillna(close.iloc[0])
        high = pd.concat([open_, close], axis=1).max(axis=1) * (1 + rng.uniform(0.0, 0.005, len(index)))
        low = pd.concat([open_, close], axis=1).min(axis=1) * (1 - rng.uniform(0.0, 0.005, len(index)))
        volume = rng.integers(100, 1000, size=len(index))

        bars = pd.DataFrame(
            {
                "open": open_.values,
                "high": high.values,
                "low": low.values,
                "close": close.values,
                "volume": volume,
            },
            index=index,
        )
        return bars.sort_index()


def _to_pandas_freq(timeframe: str) -> str:
    mapping = {
        "1m": "1min",
        "5m": "5min",
        "15m": "15min",
        "1h": "1H",
        "4h": "4H",
        "1d": "1D",
    }
    if timeframe not in mapping:
        raise KeyError(f"Unsupported timeframe: {timeframe}")
    return mapping[timeframe]
