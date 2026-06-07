from __future__ import annotations

import numpy as np
import pandas as pd

from core.indicators.ta_utils import rma


def _nz(series: pd.Series, value: float = 0.0) -> pd.Series:
    return series.fillna(value)


class _SyntheticBar:
    """
    Reproduces the Pine Script synthetic bar construct used by SuperTrend Period+.

    Pine:
        bar.new(nz(src[1]), max(nz(src[1]), src), min(nz(src[1]), src), src)
    """

    def __init__(self, source: pd.Series) -> None:
        prev = _nz(source.shift(1))
        self.o = prev
        self.h = pd.concat([prev, source], axis=1).max(axis=1)
        self.l = pd.concat([prev, source], axis=1).min(axis=1)
        self.c = source

    def _get_source(self, kind: str) -> pd.Series:
        match kind:
            case "oc2":
                return (self.o + self.c) / 2.0
            case "hl2":
                return (self.h + self.l) / 2.0
            case "hlc3":
                return (self.h + self.l + self.c) / 3.0
            case "ohlc4":
                return (self.o + self.h + self.l + self.c) / 4.0
            case "hlcc4":
                return (self.h + self.l + self.c + self.c) / 4.0
            case _:
                raise ValueError(f"Unsupported synthetic source kind: {kind}")

    def _atr(self, length: int) -> pd.Series:
        prev_h = self.h.shift(1)
        prev_c = self.c.shift(1)
        tr_first = self.h - self.l
        tr_normal = pd.concat(
            [self.h - self.l, (self.h - prev_c).abs(), (self.l - prev_c).abs()],
            axis=1,
        ).max(axis=1)
        tr = tr_normal.where(prev_h.notna(), tr_first)
        return tr if length == 1 else rma(tr, length)

    def supertrend(self, factor: float, length: int) -> tuple[pd.Series, pd.Series]:
        atr_values = self._atr(length).to_numpy(dtype=float)
        hl2 = self._get_source("hl2")
        basic_up = (hl2 + factor * self._atr(length)).to_numpy(dtype=float)
        basic_dn = (hl2 - factor * self._atr(length)).to_numpy(dtype=float)
        close_values = self.c.to_numpy(dtype=float)

        n = len(self.c)
        final_up = np.full(n, np.nan, dtype=float)
        final_dn = np.full(n, np.nan, dtype=float)
        st_value = np.full(n, np.nan, dtype=float)
        st_direction = np.full(n, np.nan, dtype=float)

        for i in range(n):
            up = basic_up[i]
            dn = basic_dn[i]
            prev_up = final_up[i - 1] if i > 0 else np.nan
            prev_dn = final_dn[i - 1] if i > 0 else np.nan
            prev_st = st_value[i - 1] if i > 0 else np.nan
            prev_close = close_values[i - 1] if i > 0 else np.nan
            prev_atr = atr_values[i - 1] if i > 0 else np.nan

            nz_prev_up = 0.0 if np.isnan(prev_up) else prev_up
            final_up[i] = up if (up < nz_prev_up or prev_close > nz_prev_up) else nz_prev_up

            nz_prev_dn = 0.0 if np.isnan(prev_dn) else prev_dn
            final_dn[i] = dn if (dn > nz_prev_dn or prev_close < nz_prev_dn) else nz_prev_dn

            if np.isnan(prev_atr):
                direction = 1.0
            elif prev_st == nz_prev_up:
                direction = -1.0 if close_values[i] > final_up[i] else 1.0
            else:
                direction = 1.0 if close_values[i] < final_dn[i] else -1.0

            st_direction[i] = direction
            st_value[i] = final_dn[i] if direction == -1.0 else final_up[i]

        return (
            pd.Series(st_value, index=self.c.index, name="st_value"),
            pd.Series(st_direction, index=self.c.index, name="st_direction").astype("Int64"),
        )


def add_super_trend(
    df: pd.DataFrame,
    length: int = 10,
    factor: float = 5.0,
    source: str = "close",
    value_col: str = "st_value",
    direction_col: str = "st_direction",
) -> pd.DataFrame:
    """
    SuperTrend Period+ translated from Pine Script.

    Causality: st_value[t] and st_direction[t] only depend on rows[:t+1].
    """
    if source not in df.columns:
        raise ValueError(f"source column not found: {source}")

    out = df.copy()
    source_series = pd.to_numeric(out[source], errors="coerce")
    bar = _SyntheticBar(source_series)
    st_value, st_direction = bar.supertrend(factor=factor, length=length)
    out[value_col] = st_value
    out[direction_col] = st_direction
    return out
