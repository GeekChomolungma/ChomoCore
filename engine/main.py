from __future__ import annotations

import argparse
from dataclasses import asdict
from typing import Any

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
    mode: str = config["mode"]
    symbol: str = config["symbol"]
    timeframe: str = config["timeframe"]

    pipeline = TradingPipeline.from_config(config)
    datasource = build_datasource(config)

    if mode == "backtest":
        _run_backtest(config, symbol, timeframe, pipeline, datasource)
    else:
        _run_live(config, symbol, timeframe, pipeline, datasource)


# ---------------------------------------------------------------------------
# Backtest: load full bar history, replay step-by-step in a rolling window
# ---------------------------------------------------------------------------

def _run_backtest(config, symbol, timeframe, pipeline: TradingPipeline, datasource) -> None:
    data_cfg = config.get("data", {})
    warmup_bars: int = config.get("backtest", {}).get("warmup_bars", 50)

    bars = datasource.load_bars(
        symbol=symbol,
        timeframe=timeframe,
        start=data_cfg.get("start"),
        end=data_cfg.get("end"),
    )

    broker = SimulatedBroker()
    signals: list[dict[str, Any]] = []

    for end_idx in range(warmup_bars, len(bars)):
        window = bars.iloc[: end_idx + 1]
        _, signal = pipeline.step(symbol, timeframe, window)
        broker.handle(signal)
        signals.append({
            "timestamp": signal.timestamp,
            "direction": signal.direction,
            "target_position": signal.target_position,
            "score": signal.score,
            "confidence": signal.confidence,
        })

    active_index = bars.index[warmup_bars:]
    positions = broker.position_series(index=active_index)
    forward_returns = (
        bars["close"].pct_change().shift(-1).reindex(active_index).fillna(0.0)
    )
    strategy_returns = positions.shift(1).fillna(0.0) * forward_returns
    equity_curve = (1.0 + strategy_returns).cumprod()
    metrics = compute_performance_metrics(strategy_returns, equity_curve)

    print("Backtest metrics:")
    for key, value in metrics.items():
        print(f"  {key}: {value:.6f}")
    print(equity_summary(equity_curve))


# ---------------------------------------------------------------------------
# Live: load latest N bars (indicator warmup window), run one step
# ---------------------------------------------------------------------------

def _run_live(config, symbol, timeframe, pipeline: TradingPipeline, datasource) -> None:
    data_cfg = config.get("data", {})
    exec_cfg = config.get("execution", {})
    window_size: int = data_cfg.get("window_size", 200)

    bars = datasource.load_latest(symbol=symbol, timeframe=timeframe, n=window_size)

    state = PositionState()
    executor = HttpSignalExecutor(
        endpoint=exec_cfg.get("endpoint", "http://localhost:8080/signal"),
        timeout=exec_cfg.get("timeout", 3.0),
        dry_run=exec_cfg.get("dry_run", True),
    )

    _, signal = pipeline.step(symbol, timeframe, bars)
    state.update(signal)
    execution = executor.handle(signal)

    print({
        "signal": {**asdict(signal), "timestamp": signal.timestamp.isoformat()},
        "execution": execution,
        "position": state.get(symbol),
    })


if __name__ == "__main__":
    main()
