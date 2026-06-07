from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


def load_config(path: str) -> dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as fh:
        cfg = yaml.safe_load(fh)

    mode = cfg.get("mode")
    if mode not in {"live", "backtest"}:
        raise ValueError(f"config must specify mode: 'live' or 'backtest', got: {mode!r}")

    return cfg
