from __future__ import annotations

import argparse
from pathlib import Path

import yaml

from quant_backtest.data.synthetic import SyntheticOHLCVDataSource
from quant_core.strategies import ma_cross  # noqa: F401
from quant_core.strategies import rsi  # noqa: F401
from quant_core.strategies.registry import StrategyRegistry
from quant_live.data.redis_source import RedisLikeDataSource
from quant_live.runtime.engine import LiveTradingEngine
from quant_live.transport.http_executor import HttpSignalExecutor


def load_config(path: str) -> dict:
    with Path(path).open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the live trading engine skeleton.")
    parser.add_argument("--config", default="configs/live/example.yaml")
    args = parser.parse_args()

    config = load_config(args.config)
    strategy = StrategyRegistry.create(config["strategy"]["name"], **config["strategy"].get("params", {}))
    bars = SyntheticOHLCVDataSource(
        periods=config["data"].get("periods", 200),
        seed=config["data"].get("seed", 7),
    ).load_bars(symbol=config["symbol"], timeframe=config["timeframe"], start=config["data"].get("start"))

    engine = LiveTradingEngine(
        strategy=strategy,
        datasource=RedisLikeDataSource(bars=bars),
        executor=HttpSignalExecutor(
            endpoint=config["execution"]["endpoint"],
            timeout=config["execution"].get("timeout", 3.0),
            dry_run=config["execution"].get("dry_run", True),
        ),
    )

    result = engine.step(symbol=config["symbol"], timeframe=config["timeframe"])
    print(result)


if __name__ == "__main__":
    main()
