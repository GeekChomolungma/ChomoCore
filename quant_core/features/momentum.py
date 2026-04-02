from __future__ import annotations

import pandas as pd


def add_momentum_features(bars: pd.DataFrame, lookbacks: tuple[int, ...] = (5, 10, 20)) -> pd.DataFrame:
    frame = bars.copy()
    for lookback in lookbacks:
        frame[f"return_{lookback}"] = frame["close"].pct_change(lookback)
        frame[f"momentum_{lookback}"] = frame["close"] / frame["close"].shift(lookback) - 1.0
    return frame
