from __future__ import annotations

import math

import pandas as pd


def compute_performance_metrics(strategy_returns: pd.Series, equity_curve: pd.Series) -> dict[str, float]:
    returns = strategy_returns.fillna(0.0)
    if returns.empty:
        return {"total_return": 0.0, "annualized_return": 0.0, "sharpe": 0.0, "max_drawdown": 0.0}

    total_return = float(equity_curve.iloc[-1] - 1.0)
    periods_per_year = 252
    annualized_return = float((equity_curve.iloc[-1] ** (periods_per_year / max(len(equity_curve), 1))) - 1.0)
    volatility = float(returns.std())
    sharpe = float((returns.mean() / volatility) * math.sqrt(periods_per_year)) if volatility > 0 else 0.0
    rolling_max = equity_curve.cummax()
    drawdown = equity_curve / rolling_max - 1.0
    max_drawdown = float(drawdown.min())
    return {
        "total_return": total_return,
        "annualized_return": annualized_return,
        "sharpe": sharpe,
        "max_drawdown": max_drawdown,
    }
