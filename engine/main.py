from __future__ import annotations

import argparse

import core.strategies.ma_cross  # noqa: F401 — register strategy
import core.strategies.rsi  # noqa: F401 — register strategy
from core.strategies.registry import StrategyRegistry
from engine.config import build_mongo_repo, load_config
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

    # Build KlineRepository once; both runners consume it via their adapters.
    kline_repo = build_mongo_repo(config)

    if mode == "backtest":
        _run_backtest(config, symbol, timeframe, strategy, indicator_pipeline, kline_repo)
    else:
        _run_live(config, symbol, timeframe, strategy, indicator_pipeline, kline_repo)


def _run_backtest(config, symbol, timeframe, strategy, indicator_pipeline, kline_repo) -> None:
    from backtest.runner import BacktestRunner

    data_cfg = config.get("data", {})

    if kline_repo is not None:
        from backtest.data.mongo_source import MongoHistoricalDataSource
        datasource = MongoHistoricalDataSource(kline_repo)
    else:
        from backtest.data.synthetic import SyntheticOHLCVDataSource
        datasource = SyntheticOHLCVDataSource(
            periods=data_cfg.get("periods", 300),
            seed=data_cfg.get("seed", 7),
        )

    bars = datasource.load_bars(
        symbol=symbol,
        timeframe=timeframe,
        start=data_cfg.get("start"),
        end=data_cfg.get("end"),
    )

    runner = BacktestRunner(
        strategy=strategy,
        indicator_pipeline=indicator_pipeline,
        warmup_bars=config.get("backtest", {}).get("warmup_bars", 50),
    )
    result = runner.run(symbol=symbol, timeframe=timeframe, bars=bars)
    runner.report(result)


def _run_live(config, symbol, timeframe, strategy, indicator_pipeline, kline_repo) -> None:
    from live.runner import LiveRunner
    from live.transport.http_executor import HttpSignalExecutor

    exec_cfg = config.get("execution", {})
    data_cfg = config.get("data", {})

    if kline_repo is not None:
        from live.data.mongo_source import MongoLiveDataSource
        datasource = MongoLiveDataSource(
            repo=kline_repo,
            window_size=data_cfg.get("window_size", 200),
        )
    else:
        # Dev fallback: synthetic data standing in for Redis/Mongo.
        from backtest.data.synthetic import SyntheticOHLCVDataSource
        from live.data.redis_source import RedisLiveDataSource
        bars = SyntheticOHLCVDataSource(
            periods=data_cfg.get("periods", 200),
            seed=data_cfg.get("seed", 7),
        ).load_bars(symbol=symbol, timeframe=timeframe, start=data_cfg.get("start"))
        datasource = RedisLiveDataSource(bars=bars)

    runner = LiveRunner(
        strategy=strategy,
        indicator_pipeline=indicator_pipeline,
        datasource=datasource,
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
