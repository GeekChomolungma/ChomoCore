from __future__ import annotations

import pandas as pd

from core.indicators.ta_utils import rma


def add_rsi(
    df: pd.DataFrame,
    length: int = 14,
    source: str = "close",
    output_col: str | None = None,
) -> pd.DataFrame:
    if source not in df.columns:
        raise ValueError(f"source column not found: {source}")

    col = output_col or f"rsi_{length}"
    out = df.copy()

    change = out[source].diff()
    gain = change.clip(lower=0)
    loss = -change.clip(upper=0)

    avg_gain = rma(gain, length)
    avg_loss = rma(loss, length)

    rs = avg_gain / avg_loss
    out[col] = 100 - (100 / (1 + rs))

    out.loc[avg_loss == 0, col] = 100
    out.loc[avg_gain == 0, col] = 0
    out.loc[(avg_gain == 0) & (avg_loss == 0), col] = 50

    return out
