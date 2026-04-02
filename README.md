# Quant Strategy Infrastructure

This repository provides a modular quantitative trading foundation built around a unified market context and strategy signal contract.

## Project Layout

```text
project/
├─ quant_core/
│  ├─ context/
│  │  └─ market_context.py
│  ├─ signal/
│  │  └─ signal.py
│  ├─ strategies/
│  │  ├─ base.py
│  │  ├─ rsi.py
│  │  └─ ma_cross.py
│  ├─ features/
│  │  ├─ momentum.py
│  │  ├─ volatility.py
│  │  └─ ta.py
│  └─ utils/
│
├─ quant_backtest/
│  ├─ data/
│  ├─ replay/
│  ├─ broker/
│  ├─ metrics/
│  ├─ plots/
│  └─ main.py
│
├─ quant_live/
│  ├─ data/
│  ├─ runtime/
│  ├─ transport/
│  ├─ state/
│  └─ main.py
│
├─ configs/
│  ├─ backtest/
│  └─ live/
└─ pyproject.toml
```

## Core Contract

`quant_core` is the canonical boundary between upstream market data, pluggable strategy logic, and downstream execution or replay systems.

### `MarketContext`

`MarketContext` is the standardized input for all strategies.

Required `bars` contract:

- columns must include `open`, `high`, `low`, `close`, `volume`
- index must be a `pd.DatetimeIndex`
- rows must be sorted in ascending time order
- the last row timestamp must equal `timestamp`
- data is expected to be pre-cleaned, deduplicated, aligned, and ready for strategy consumption

Optional `bars` columns:

- `quote_volume`
- `trade_count`
- `taker_buy_volume`
- `is_closed`

### `StrategySignal`

Every strategy returns a normalized signal with:

- `direction`: `long`, `short`, or `flat`
- `target_position`: normalized exposure in `[-1.0, 1.0]`
- optional `score`, `confidence`, and `meta`

## Extension Points

- Add new hand-crafted strategies by subclassing `BaseStrategy`
- Add predictive models by building features from `MarketContext` and wrapping model output into `StrategySignal`
- Register strategies with `StrategyRegistry` so they can be instantiated from config
- Connect Mongo historical data and Redis real-time data by implementing the provider interfaces in `quant_backtest.data` and `quant_live.data`

## Quick Start

Install dependencies:

```bash
pip install -e .
```

Run the demo backtest:

```bash
python -m quant_backtest.main --config configs/backtest/example.yaml
```

Run the live engine skeleton:

```bash
python -m quant_live.main --config configs/live/example.yaml
```

## Notes

- The current backtest and live modules are intentionally lightweight scaffolds.
- Data-source adapters for Mongo and Redis are abstracted and can be replaced without changing strategy code.
- The live executor sends normalized signals to downstream systems over HTTP.
