from __future__ import annotations

import pandas as pd


def add_volatility_features(bars: pd.DataFrame, lookbacks: tuple[int, ...] = (10, 20, 50)) -> pd.DataFrame:
    frame = bars.copy()
    returns = frame["close"].pct_change()
    for lookback in lookbacks:
        frame[f"volatility_{lookback}"] = returns.rolling(lookback).std()
    return frame
