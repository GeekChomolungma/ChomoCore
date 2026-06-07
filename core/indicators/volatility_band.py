from __future__ import annotations

import pandas as pd

from core.indicators.ta_utils import sma, stdev, atr


def add_volatility_band(
    df: pd.DataFrame,
    length: int = 20,
    mult: float = 2.0,
    atr_mult: float = 1.5,
    source: str = "close",
    upper_col: str = "reversal_upper",
    lower_col: str = "reversal_lower",
) -> pd.DataFrame:
    """
    Volatility Reversion Bands (translated from Pine Script).

    Pine core:
        basis         = ta.sma(close, length)
        bbUpper       = basis + ta.stdev(close, length) * mult
        bbLower       = basis - ta.stdev(close, length) * mult
        atrBand       = ta.atr(length) * atrMult
        reversalUpper = bbUpper + atrBand
        reversalLower = bbLower - atrBand

    Causality: reversal_upper[t] and reversal_lower[t] only depend on rows[:t+1].
    """
    required = [source, "high", "low", "close"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"missing columns: {missing}")

    out = df.copy()
    src = pd.to_numeric(out[source], errors="coerce")

    basis = sma(src, length)
    std = stdev(src, length)
    bb_upper = basis + std * mult
    bb_lower = basis - std * mult
    atr_band = atr(
        pd.to_numeric(out["high"], errors="coerce"),
        pd.to_numeric(out["low"], errors="coerce"),
        pd.to_numeric(out["close"], errors="coerce"),
        length,
    ) * atr_mult

    out[upper_col] = bb_upper + atr_band
    out[lower_col] = bb_lower - atr_band
    return out
