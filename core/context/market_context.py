from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pandas as pd

from core.utils.validation import validate_market_context


@dataclass(slots=True)
class MarketContext:
    symbol: str
    timeframe: str
    timestamp: pd.Timestamp
    bars: pd.DataFrame
    features: dict[str, Any] | None = None
    market_meta: dict[str, Any] | None = None

    def __post_init__(self) -> None:
        self.timestamp = pd.Timestamp(self.timestamp)
        validate_market_context(self)

    @property
    def latest_bar(self) -> pd.Series:
        return self.bars.iloc[-1]
