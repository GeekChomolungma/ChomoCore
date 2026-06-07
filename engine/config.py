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


def build_mongo_repo(cfg: dict[str, Any]):
    """
    Construct a KlineRepository from the `mongo` config section.

    Returns None if no `mongo` section is present (caller falls back to
    synthetic data).

    Expected config shape:
        mongo:
          uri: mongodb://localhost:27017
          db: market_info
          exchange: Binance   # optional, default Binance
    """
    if "mongo" not in cfg:
        return None

    from infra.mongo.client import MongoClientFactory
    from infra.mongo.kline_repo import KlineRepository

    mongo_cfg = cfg["mongo"]
    db = MongoClientFactory.get_db(
        uri=mongo_cfg["uri"],
        db_name=mongo_cfg.get("db", "market_info"),
    )
    return KlineRepository(db, exchange=mongo_cfg.get("exchange", "Binance"))
