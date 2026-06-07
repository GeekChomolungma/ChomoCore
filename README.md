# ChomoCore

Modular quantitative trading infrastructure. One unified pipeline for both live trading and backtesting, switched by a single `mode` field in the config.

## Package Layout

```text
chomocore/
├── core/                    # canonical contracts — no I/O, no mode awareness
│   ├── context/             # MarketContext
│   ├── signal/              # StrategySignal
│   ├── indicators/          # pluggable indicator functions + registry
│   ├── strategies/          # BaseStrategy + StrategyRegistry + built-ins
│   ├── execution/           # BaseExecutor contract
│   └── utils/               # validation helpers
│
├── pipeline/                # mode-agnostic pipeline wiring
│   ├── indicator_pipeline.py
│   ├── context_builder.py
│   └── runner.py            # TradingPipeline (shared by live & backtest)
│
├── backtest/                # replay-mode components
│   ├── data/                # HistoricalDataSource (Mongo placeholder + synthetic)
│   ├── broker/              # SimulatedBroker
│   ├── metrics/             # performance metrics
│   ├── plots/               # equity curve summary
│   └── runner.py            # BacktestRunner
│
├── live/                    # live-mode components
│   ├── data/                # LiveDataSource (Redis placeholder + Mongo placeholder)
│   ├── state/               # PositionState
│   ├── transport/           # HttpSignalExecutor
│   └── runner.py            # LiveRunner
│
├── engine/                  # unified CLI entry point
│   ├── config.py
│   └── main.py
│
└── configs/
    ├── backtest/example.yaml
    └── live/example.yaml
```

---

## Pipeline Architecture

Both modes share the same 5-layer pipeline. The only difference is how bars are sourced and how signals are executed.

```text
 ┌──────────────────────────────────────────────────────────────────────┐
 │                        UNIFIED PIPELINE                              │
 │                                                                      │
 │  ① Raw Data         ② Indicators        ③ MarketContext              │
 │  ┌──────────┐       ┌──────────────┐     ┌───────────────────────┐   │
 │  │ OHLCV    │──────▶│ super_trend  │───▶│ MarketContext         │   │
 │  │ bars     │       │  RSI         │     │  .symbol              │   │
 │  │ (window) │       │  vol_band    │     │  .timeframe           │   │
 │  └──────────┘       │  ...         │     │  .timestamp           │   │
 │                     └──────────────┘     │  .bars   (enriched)   │   │
 │                                          │  .features (indicator)│   │
 │                                          └───────────────────────┘   │
 │                                                                      │
 │                                                                      │
 │  ④ Strategy                           ⑤ Execution                    │
 │  ┌──────────────────────┐             ┌───────────────────────────┐  │
 │  │ BaseStrategy         │             │ BaseExecutor              │  │
 │  │  .evaluate(context)  │────signal──▶│                          │  │ 
 │  │                      │             │ live     → HTTP POST      │  │
 │  │  StrategySignal:     │             │ backtest → SimulatedBroker│  │
 │  │   direction          │             │          (record only)    │  │
 │  │   target_position    │             └───────────────────────────┘  │
 │  │   score / confidence │                                            │
 │  └──────────────────────┘                                            │
 └──────────────────────────────────────────────────────────────────────┘
```

---

## Layer Details

### 1. Raw Data Layer

#### Live mode

- Closed K-lines are stored in MongoDB (producer already implemented externally).
- The in-progress (open) K-line is held in Redis.
- `live.data.RedisLiveDataSource` fetches the latest rolling window and returns it as a plain `pd.DataFrame`.

#### Backtest mode

- `backtest.data.MongoHistoricalDataSource` loads closed K-lines from MongoDB (placeholder — schema TBD).
- `backtest.data.SyntheticOHLCVDataSource` generates random-walk OHLCV for local development.

**Required bar columns:** `open`, `high`, `low`, `close`, `volume`
**Index:** `pd.DatetimeIndex`, ascending, no duplicates.

---

### 2. Indicator Layer

Indicators are pure functions with the signature:

```python
def add_xxx(df: pd.DataFrame, **params) -> pd.DataFrame:
    ...  # return df with new columns appended
```

**Causality rule:** `indicator[t]` must depend only on `rows[0:t+1]`. No centered windows, no future leakage.

Built-in indicators (in `core/indicators/`):

| Name | Output columns | Key params |
| --- | --- | --- |
| `rsi` | `rsi_{length}` | `length`, `source` |
| `super_trend` | `st_value`, `st_direction` | `length`, `factor`, `source` |
| `volatility_band` | `reversal_upper`, `reversal_lower` | `length`, `mult`, `atr_mult` |

Add a custom indicator:

```python
from core.indicators import register_indicator

def add_my_indicator(df, window=20):
    out = df.copy()
    out["my_col"] = df["close"].rolling(window).mean()
    return out

register_indicator("my_indicator", add_my_indicator)
```

Configure in YAML:

```yaml
indicators:
  - name: rsi
    params:
      length: 14
  - name: my_indicator
    params:
      window: 20
```

`IndicatorPipeline` applies specs in order, so each indicator can reference columns added by earlier ones.

---

### 3. MarketContext (State Layer)

`MarketContext` is the central state object passed to every strategy:

```python
@dataclass
class MarketContext:
    symbol: str
    timeframe: str
    timestamp: pd.Timestamp
    bars: pd.DataFrame       # OHLCV + all indicator columns (full history window)
    features: dict | None    # latest value of each indicator column (O(1) access)
    market_meta: dict | None # source metadata (e.g. {"source": "redis"})
```

`features` gives strategies quick scalar access (`context.features["rsi_14"]`) while `bars` gives the full series for strategies that need historical depth.

---

### 4. Strategy & Signal Layer

Implement a strategy by subclassing `BaseStrategy`:

```python
from core.strategies.base import BaseStrategy
from core.strategies.registry import StrategyRegistry
from core.signal.signal import StrategySignal

@StrategyRegistry.register("my_strategy")
class MyStrategy(BaseStrategy):
    def __init__(self, threshold: float = 0.5):
        super().__init__("my_strategy")
        self.threshold = threshold

    def evaluate(self, context: MarketContext) -> StrategySignal:
        rsi = context.features["rsi_14"]
        direction = "long" if rsi < self.threshold else "flat"
        ...
```

`StrategySignal` fields:

| Field | Type | Meaning |
| --- | --- | --- |
| `direction` | `"long"` / `"short"` / `"flat"` | trade intent |
| `target_position` | `float` in `[-1.0, 1.0]` | normalised exposure |
| `score` | `float \| None` | raw indicator score |
| `confidence` | `float \| None` | clamped to `[0, 1]` |
| `meta` | `dict \| None` | arbitrary strategy debug info |

---

### 5. Execution Layer

| Mode | Executor | Behaviour |
| --- | --- | --- |
| `live` | `HttpSignalExecutor` | POST signal JSON to downstream endpoint; `dry_run=true` skips HTTP |
| `backtest` | `SimulatedBroker` | Records target positions; builds equity curve after loop |

Both implement `BaseExecutor.handle(signal) -> dict`.

---

## Quick Start

Install:

```bash
pip install -e .
```

Run backtest:

```bash
python -m engine.main --config configs/backtest/example.yaml
```

Run live engine (dry-run):

```bash
python -m engine.main --config configs/live/example.yaml
```

---

## Extension Points

| Goal | Where |
| --- | --- |
| New indicator | Add function to `core/indicators/`, call `register_indicator()` |
| New strategy | Subclass `BaseStrategy`, decorate with `@StrategyRegistry.register("name")` |
| Connect real MongoDB | Implement `backtest.data.MongoHistoricalDataSource.load_bars()` |
| Connect real Redis | Implement `live.data.RedisLiveDataSource.get_latest_context()` |
| Real order execution | Subclass `BaseExecutor`, set `dry_run=false` or replace executor in config |
| Indicator persistence | Add a `persistence` hook after `IndicatorPipeline.apply()` in `TradingPipeline.step()` |

---

## Design Constraints

- **No look-ahead bias.** All indicator functions must satisfy `indicator[t] = f(rows[0:t+1])`.
- **Mode is config, not code.** Live and backtest share `TradingPipeline`. Switching modes changes only the data source and executor, not any strategy or indicator logic.
- **`core/` has no I/O.** Nothing in `core/` reads files, talks to Redis/Mongo, or makes HTTP calls. It is safe to import in any context.
