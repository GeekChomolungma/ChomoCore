from __future__ import annotations

import argparse
from dataclasses import asdict
from typing import Any

import pandas as pd

import core.strategies.ma_cross  # noqa: F401 — register strategy
import core.strategies.rsi  # noqa: F401 — register strategy
from backtest.broker.simulated import SimulatedBroker
from backtest.metrics.performance import compute_performance_metrics
from backtest.plots.equity import equity_summary
from engine.config import build_datasource, load_config
from live.state.position_state import PositionState
from live.transport.http_executor import HttpSignalExecutor
from pipeline.runner import TradingPipeline


def main() -> None:
    parser = argparse.ArgumentParser(description="ChomoCore unified trading engine.")
    parser.add_argument("--config", required=True, help="Path to YAML config file.")
    args = parser.parse_args()

    config = load_config(args.config)
    pipeline = TradingPipeline.from_config(config)
    datasource = build_datasource(config)

    if config["mode"] == "backtest":
        _run_backtest(config, pipeline, datasource)
    else:
        _run_live(config, pipeline, datasource)


# ---------------------------------------------------------------------------
# Backtest: replay primary context bar-by-bar; slice all other contexts by
# timestamp so different timeframes stay causal.
# ---------------------------------------------------------------------------

def _run_backtest(config, pipeline: TradingPipeline, datasource) -> None:
    data_cfg = config.get("data", {})
    warmup_bars: int = config.get("backtest", {}).get("warmup_bars", 50)

    # Load full bar history for every declared context.
    all_bars: dict[tuple[str, str], pd.DataFrame] = {
        (spec.symbol, spec.timeframe): datasource.load_bars(
            symbol=spec.symbol,
            timeframe=spec.timeframe,
            start=data_cfg.get("start"),
            end=data_cfg.get("end"),
        )
        for spec in pipeline.context_specs
    }

    primary = pipeline.primary_spec
    primary_bars = all_bars[(primary.symbol, primary.timeframe)]

    broker = SimulatedBroker()
    signals: list[dict[str, Any]] = []

    for end_idx in range(warmup_bars, len(primary_bars)):
        current_ts: pd.Timestamp = primary_bars.index[end_idx]

        bars_map: dict[tuple[str, str], pd.DataFrame] = {}
        for spec in pipeline.context_specs:
            key = (spec.symbol, spec.timeframe)
            bars = all_bars[key]
            if key == (primary.symbol, primary.timeframe):
                # Primary: row-based window
                bars_map[key] = bars.iloc[: end_idx + 1]
            else:
                # Other contexts: include all bars whose starttime <= current bar
                window = bars[bars.index <= current_ts]
                if not window.empty:
                    bars_map[key] = window

        if len(bars_map) < len(pipeline.context_specs):
            # Some non-primary context has no data yet; skip until warmup complete
            continue

        _, signal = pipeline.step(bars_map)
        broker.handle(signal)
        signals.append({
            "timestamp": signal.timestamp,
            "direction": signal.direction,
            "target_position": signal.target_position,
            "score": signal.score,
            "confidence": signal.confidence,
        })

    active_index = primary_bars.index[warmup_bars:]
    positions = broker.position_series(index=active_index)
    forward_returns = (
        primary_bars["close"].pct_change().shift(-1).reindex(active_index).fillna(0.0)
    )
    strategy_returns = positions.shift(1).fillna(0.0) * forward_returns
    equity_curve = (1.0 + strategy_returns).cumprod()
    metrics = compute_performance_metrics(strategy_returns, equity_curve)

    print("Backtest metrics:")
    for key, value in metrics.items():
        print(f"  {key}: {value:.6f}")
    print(equity_summary(equity_curve))


# ---------------------------------------------------------------------------
# Live: load latest N bars per context (indicator warmup window), one step.
# ---------------------------------------------------------------------------

def _run_live(config, pipeline: TradingPipeline, datasource) -> None:
    data_cfg = config.get("data", {})
    exec_cfg = config.get("execution", {})
    window_size: int = data_cfg.get("window_size", 200)

    bars_map: dict[tuple[str, str], pd.DataFrame] = {
        (spec.symbol, spec.timeframe): datasource.load_latest(
            symbol=spec.symbol,
            timeframe=spec.timeframe,
            n=window_size,
        )
        for spec in pipeline.context_specs
    }

    state = PositionState()
    executor = HttpSignalExecutor(
        endpoint=exec_cfg.get("endpoint", "http://localhost:8080/signal"),
        timeout=exec_cfg.get("timeout", 3.0),
        dry_run=exec_cfg.get("dry_run", True),
    )

    _, signal = pipeline.step(bars_map)
    state.update(signal)
    execution = executor.handle(signal)

    print({
        "signal": {**asdict(signal), "timestamp": signal.timestamp.isoformat()},
        "execution": execution,
        "position": state.get(signal.symbol),
    })


if __name__ == "__main__":
    main()
