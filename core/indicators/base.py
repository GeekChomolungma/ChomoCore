from __future__ import annotations

from typing import Protocol

import pandas as pd


class IndicatorFn(Protocol):
    """
    Signature contract for all indicator functions.

    An indicator function receives a OHLCV (or already-enriched) DataFrame
    and returns a new DataFrame with one or more additional columns appended.
    All computation must be strictly causal: indicator[t] may only depend on
    rows[0:t+1]. See indicators/__init__.py for the full causality protocol.
    """

    def __call__(self, df: pd.DataFrame, **kwargs: object) -> pd.DataFrame: ...
