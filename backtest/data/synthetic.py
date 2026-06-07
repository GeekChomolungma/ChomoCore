from __future__ import annotations

import numpy as np
import pandas as pd

from backtest.data.base import HistoricalDataSource


_TIMEFRAME_FREQ: dict[str, str] = {
    "1m": "1min",
    "5m": "5min",
    "15m": "15min",
    "1h": "1h",
    "4h": "4h",
    "1d": "1D",
}


class SyntheticOHLCVDataSource(HistoricalDataSource):
    def __init__(self, periods: int = 300, seed: int = 7) -> None:
        self.periods = periods
        self.seed = seed

    def load_bars(
        self,
        symbol: str,
        timeframe: str,
        start: str | None = None,
        end: str | None = None,
    ) -> pd.DataFrame:
        if timeframe not in _TIMEFRAME_FREQ:
            raise KeyError(f"Unsupported timeframe: {timeframe}")

        rng = np.random.default_rng(self.seed)
        index = pd.date_range(
            start=start or "2024-01-01",
            periods=self.periods,
            freq=_TIMEFRAME_FREQ[timeframe],
        )
        returns = rng.normal(loc=0.0005, scale=0.01, size=len(index))
        close = 100 * (1 + pd.Series(returns, index=index)).cumprod()
        open_ = close.shift(1).fillna(close.iloc[0])
        high = pd.concat([open_, close], axis=1).max(axis=1) * (
            1 + rng.uniform(0.0, 0.005, len(index))
        )
        low = pd.concat([open_, close], axis=1).min(axis=1) * (
            1 - rng.uniform(0.0, 0.005, len(index))
        )
        volume = rng.integers(100, 1000, size=len(index)).astype(float)

        return pd.DataFrame(
            {"open": open_.values, "high": high.values, "low": low.values,
             "close": close.values, "volume": volume},
            index=index,
        ).sort_index()
