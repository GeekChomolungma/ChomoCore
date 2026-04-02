from __future__ import annotations

import argparse
from pathlib import Path

import yaml

from quant_backtest.data.synthetic import SyntheticOHLCVDataSource
from quant_backtest.plots.equity import equity_summary
from quant_backtest.replay.engine import BacktestEngine
from quant_core.strategies import ma_cross  # noqa: F401
from quant_core.strategies import rsi  # noqa: F401
from quant_core.strategies.registry import StrategyRegistry


def load_config(path: str) -> dict:
    with Path(path).open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a quant backtest.")
    parser.add_argument("--config", default="configs/backtest/example.yaml")
    args = parser.parse_args()

    config = load_config(args.config)
    strategy = StrategyRegistry.create(config["strategy"]["name"], **config["strategy"].get("params", {}))

    datasource = SyntheticOHLCVDataSource(
        periods=config["data"].get("periods", 300),
        seed=config["data"].get("seed", 7),
    )
    bars = datasource.load_bars(
        symbol=config["symbol"],
        timeframe=config["timeframe"],
        start=config["data"].get("start"),
    )

    result = BacktestEngine(strategy=strategy, warmup_bars=config["backtest"].get("warmup_bars", 50)).run(
        symbol=config["symbol"],
        timeframe=config["timeframe"],
        bars=bars,
    )

    print("Backtest metrics:")
    for key, value in result.metrics.items():
        print(f"  {key}: {value:.6f}")
    print(equity_summary(result.equity_curve))


if __name__ == "__main__":
    main()
