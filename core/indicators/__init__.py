"""
=====================================================================
Time Alignment & No-Lookahead Protocol

All indicator functions in this package must be strictly causal.

Index definition:
    row[0] = earliest observation (ascending time order)
    row[t] = the (t+1)-th observation

Causality rule:
    indicator[t] = f(rows[0:t+1])   — strictly no future data

Decision timing:
    A signal computed from indicator[t] may only be ACTED ON at
    the beginning of row[t+1] or later.

Any violation of this protocol invalidates backtest correctness.
=====================================================================
"""

from __future__ import annotations

from typing import Any

import pandas as pd

from core.indicators.base import IndicatorFn
from core.indicators.rsi import add_rsi
from core.indicators.super_trend import add_super_trend
from core.indicators.volatility_band import add_volatility_band

INDICATOR_REGISTRY: dict[str, IndicatorFn] = {
    "rsi": add_rsi,
    "super_trend": add_super_trend,
    "volatility_band": add_volatility_band,
}


def apply_indicator(df: pd.DataFrame, name: str, **params: Any) -> pd.DataFrame:
    if name not in INDICATOR_REGISTRY:
        available = ", ".join(sorted(INDICATOR_REGISTRY))
        raise ValueError(f"Unknown indicator: '{name}'. Available: {available}")
    return INDICATOR_REGISTRY[name](df, **params)


def register_indicator(name: str, fn: IndicatorFn) -> None:
    """Register a custom indicator function at runtime."""
    INDICATOR_REGISTRY[name] = fn
