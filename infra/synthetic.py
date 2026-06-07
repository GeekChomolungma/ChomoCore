from __future__ import annotations

import numpy as np
import pandas as pd


_TIMEFRAME_FREQ: dict[str, str] = {
    "1m": "1min",
    "5m": "5min",
    "15m": "15min",
    "1h": "1h",
    "4h": "4h",
    "1d": "1D",
}


class SyntheticDataSource:
    """Random-walk OHLCV generator. For local development and unit tests only."""

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
        return self._generate(timeframe, start or "2024-01-01", self.periods)

    def load_latest(self, symbol: str, timeframe: str, n: int) -> pd.DataFrame:
        return self._generate(timeframe, "2024-01-01", n)

    def _generate(self, timeframe: str, start: str, periods: int) -> pd.DataFrame:
        if timeframe not in _TIMEFRAME_FREQ:
            raise KeyError(f"Unsupported timeframe: {timeframe}")
        rng = np.random.default_rng(self.seed)
        index = pd.date_range(start=start, periods=periods, freq=_TIMEFRAME_FREQ[timeframe])
        returns = rng.normal(loc=0.0005, scale=0.01, size=periods)
        close = 100 * (1 + pd.Series(returns, index=index)).cumprod()
        open_ = close.shift(1).fillna(close.iloc[0])
        high = pd.concat([open_, close], axis=1).max(axis=1) * (
            1 + rng.uniform(0.0, 0.005, periods)
        )
        low = pd.concat([open_, close], axis=1).min(axis=1) * (
            1 - rng.uniform(0.0, 0.005, periods)
        )
        volume = rng.integers(100, 1000, size=periods).astype(float)
        return pd.DataFrame(
            {"open": open_.values, "high": high.values, "low": low.values,
             "close": close.values, "volume": volume},
            index=index,
        )
