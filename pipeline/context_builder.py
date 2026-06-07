from __future__ import annotations

from typing import Any

import pandas as pd

from core.context.market_context import MarketContext


def build_context(
    symbol: str,
    timeframe: str,
    enriched_bars: pd.DataFrame,
    indicator_cols: list[str] | None = None,
    market_meta: dict[str, Any] | None = None,
) -> MarketContext:
    """
    Build a MarketContext from an enriched bars DataFrame.

    enriched_bars must satisfy the standard OHLCV contract (validated inside
    MarketContext.__post_init__). Indicator columns are expected to already be
    appended by IndicatorPipeline.apply().

    The features dict is populated with the latest (iloc[-1]) value of every
    indicator column, giving strategies O(1) access to current indicator state
    without having to slice the DataFrame themselves.
    """
    features: dict[str, Any] | None = None

    if indicator_cols:
        latest = enriched_bars.iloc[-1]
        features = {
            col: float(latest[col])
            for col in indicator_cols
            if col in enriched_bars.columns and pd.notna(latest[col])
        }
        if not features:
            features = None

    return MarketContext(
        symbol=symbol,
        timeframe=timeframe,
        timestamp=pd.Timestamp(enriched_bars.index[-1]),
        bars=enriched_bars,
        features=features,
        market_meta=market_meta,
    )
