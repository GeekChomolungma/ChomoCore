from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import pandas as pd

from core.indicators import INDICATOR_REGISTRY


@dataclass
class IndicatorSpec:
    name: str
    params: dict[str, Any] = field(default_factory=dict)


class IndicatorPipeline:
    """
    Applies an ordered chain of indicator functions to a bars DataFrame.

    Each indicator receives the output of the previous one, so indicators
    can reference columns produced by earlier steps in the chain.
    The pipeline tracks which columns were added so the caller can populate
    MarketContext.features without hard-coding column names.
    """

    def __init__(self, specs: list[IndicatorSpec]) -> None:
        self._specs = specs

    @classmethod
    def from_config(cls, config: list[dict[str, Any]]) -> IndicatorPipeline:
        specs = [
            IndicatorSpec(name=c["name"], params=c.get("params", {}))
            for c in config
        ]
        return cls(specs)

    def apply(self, bars: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
        """
        Returns (enriched_bars, indicator_columns).

        enriched_bars      — original OHLCV columns + all added indicator columns
        indicator_columns  — names of the columns that were added by this pipeline
        """
        original_cols: set[str] = set(bars.columns)
        result = bars

        for spec in self._specs:
            if spec.name not in INDICATOR_REGISTRY:
                available = ", ".join(sorted(INDICATOR_REGISTRY))
                raise ValueError(
                    f"Unknown indicator '{spec.name}'. Available: {available}"
                )
            result = INDICATOR_REGISTRY[spec.name](result, **spec.params)

        added = [c for c in result.columns if c not in original_cols]
        return result, added
