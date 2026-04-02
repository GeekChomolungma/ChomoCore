from __future__ import annotations

from typing import TYPE_CHECKING

import pandas as pd

if TYPE_CHECKING:
    from quant_core.context.market_context import MarketContext


REQUIRED_BAR_COLUMNS = ("open", "high", "low", "close", "volume")
OPTIONAL_BAR_COLUMNS = ("quote_volume", "trade_count", "taker_buy_volume", "is_closed")


def validate_market_context(context: "MarketContext") -> None:
    if not isinstance(context.bars, pd.DataFrame):
        raise TypeError("bars must be a pandas DataFrame")

    if context.bars.empty:
        raise ValueError("bars must not be empty")

    missing = [column for column in REQUIRED_BAR_COLUMNS if column not in context.bars.columns]
    if missing:
        raise ValueError(f"bars missing required columns: {missing}")

    if not isinstance(context.bars.index, pd.DatetimeIndex):
        raise TypeError("bars index must be a pandas DatetimeIndex")

    if not context.bars.index.is_monotonic_increasing:
        raise ValueError("bars index must be sorted in ascending time order")

    last_timestamp = pd.Timestamp(context.bars.index[-1])
    if last_timestamp != context.timestamp:
        raise ValueError(
            f"context timestamp {context.timestamp} must match the last bar index {last_timestamp}"
        )
