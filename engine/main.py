from __future__ import annotations

import argparse

import core.strategies.ma_cross  # noqa: F401 — register strategy
import core.strategies.rsi  # noqa: F401 — register strategy
from core.strategies.registry import StrategyRegistry
from engine.config import load_config
from pipeline.indicator_pipeline import IndicatorPipeline


def main() -> None:
    parser = argparse.ArgumentParser(description="ChomoCore unified trading engine.")
    parser.add_argument("--config", required=True, help="Path to YAML config file.")
    args = parser.parse_args()

    config = load_config(args.config)
    mode: str = config["mode"]
    symbol: str = config["symbol"]
    timeframe: str = config["timeframe"]

    strategy = StrategyRegistry.create(
        config["strategy"]["name"],
        **config["strategy"].get("params", {}),
    )
    indicator_pipeline = IndicatorPipeline.from_config(
        config.get("indicators", [])
    )

    if mode == "backtest":
        _run_backtest(config, symbol, timeframe, strategy, indicator_pipeline)
    else:
        _run_live(config, symbol, timeframe, strategy, indicator_pipeline)


def _run_backtest(config, symbol, timeframe, strategy, indicator_pipeline) -> None:
    from backtest.data.synthetic import SyntheticOHLCVDataSource
    from backtest.runner import BacktestRunner

    data_cfg = config.get("data", {})
    bars = SyntheticOHLCVDataSource(
        periods=data_cfg.get("periods", 300),
        seed=data_cfg.get("seed", 7),
    ).load_bars(symbol=symbol, timeframe=timeframe, start=data_cfg.get("start"))

    runner = BacktestRunner(
        strategy=strategy,
        indicator_pipeline=indicator_pipeline,
        warmup_bars=config.get("backtest", {}).get("warmup_bars", 50),
    )
    result = runner.run(symbol=symbol, timeframe=timeframe, bars=bars)
    runner.report(result)


def _run_live(config, symbol, timeframe, strategy, indicator_pipeline) -> None:
    from backtest.data.synthetic import SyntheticOHLCVDataSource
    from live.data.redis_source import RedisLiveDataSource
    from live.runner import LiveRunner
    from live.transport.http_executor import HttpSignalExecutor

    data_cfg = config.get("data", {})
    exec_cfg = config.get("execution", {})

    # Until the real Redis adapter is wired up, fall back to synthetic data
    # for local development. Replace RedisLiveDataSource with the real impl
    # once the producer protocol is confirmed.
    bars = SyntheticOHLCVDataSource(
        periods=data_cfg.get("periods", 200),
        seed=data_cfg.get("seed", 7),
    ).load_bars(symbol=symbol, timeframe=timeframe, start=data_cfg.get("start"))

    runner = LiveRunner(
        strategy=strategy,
        indicator_pipeline=indicator_pipeline,
        datasource=RedisLiveDataSource(bars=bars),
        executor=HttpSignalExecutor(
            endpoint=exec_cfg.get("endpoint", "http://localhost:8080/signal"),
            timeout=exec_cfg.get("timeout", 3.0),
            dry_run=exec_cfg.get("dry_run", True),
        ),
    )

    result = runner.step(symbol=symbol, timeframe=timeframe)
    print(result)


if __name__ == "__main__":
    main()
