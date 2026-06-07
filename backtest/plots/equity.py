from __future__ import annotations

import pandas as pd


def equity_summary(equity_curve: pd.Series) -> str:
    if equity_curve.empty:
        return "empty equity curve"
    return (
        f"start={equity_curve.index[0]} "
        f"end={equity_curve.index[-1]} "
        f"final_equity={equity_curve.iloc[-1]:.4f}"
    )
