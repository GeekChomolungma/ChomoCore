from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


def load_config(path: str) -> dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as fh:
        cfg = yaml.safe_load(fh)

    mode = cfg.get("mode")
    if mode not in {"live", "backtest"}:
        raise ValueError(
            f"config must specify mode: 'live' or 'backtest', got: {mode!r}"
        )
    return cfg


def build_datasource(cfg: dict[str, Any]):
    """
    Build a KlineRepository from the `mongo` config section.

    Expected config shape:
        mongo:
          uri: mongodb://localhost:27017
          db: market_info
          exchange: Binance   # optional, defaults to Binance

    # TODO: add a `redis` section here once the Redis producer protocol is
    # confirmed, to support a RedisDataSource for the live in-progress bar.
    """
    if "mongo" not in cfg:
        raise ValueError(
            "Missing required `mongo` section in config. "
            "Provide a MongoDB URI to use as the K-line data source."
        )

    from infra.mongo.client import MongoClientFactory
    from infra.mongo.kline_repo import KlineRepository

    m = cfg["mongo"]
    db = MongoClientFactory.get_db(uri=m["uri"], db_name=m.get("db", "market_info"))
    return KlineRepository(db, exchange=m.get("exchange", "Binance"))
