from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pandas as pd

from core.context.market_bundle import MarketBundle
from core.context.market_context import MarketContext
from core.signal.signal import StrategySignal
from core.strategies.base import BaseStrategy
from core.strategies.registry import StrategyRegistry
from pipeline.context_builder import build_context
from pipeline.indicator_pipeline import IndicatorPipeline


@dataclass
class ContextSpec:
    """
    Declares one (symbol, timeframe) slot in the pipeline, along with the
    indicator chain that enriches its bars before context assembly.
    """
    symbol: str
    timeframe: str
    indicator_pipeline: IndicatorPipeline
    is_primary: bool = False


class TradingPipeline:
    """
    Mode-agnostic pipeline: bars_map → indicators → MarketBundle → signal.

    Supports any number of (symbol, timeframe) combinations. The primary
    context is the one the resulting StrategySignal is attributed to.
    Construct via from_config() — engine only needs this single object.
    """

    def __init__(self, strategy: BaseStrategy, context_specs: list[ContextSpec]) -> None:
        primaries = [s for s in context_specs if s.is_primary]
        if len(primaries) != 1:
            raise ValueError(
                f"Exactly one context must be marked primary, got {len(primaries)}."
            )
        self.strategy = strategy
        self._specs = context_specs
        self._primary = primaries[0]

    @property
    def context_specs(self) -> list[ContextSpec]:
        return self._specs

    @property
    def primary_spec(self) -> ContextSpec:
        return self._primary

    @classmethod
    def from_config(cls, config: dict[str, Any]) -> TradingPipeline:
        strategy = StrategyRegistry.create(
            config["strategy"]["name"],
            **config["strategy"].get("params", {}),
        )

        raw = config.get("contexts", [])

        # Backward compat: old single-symbol flat config
        if not raw:
            raw = [{
                "symbol": config["symbol"],
                "timeframe": config["timeframe"],
                "primary": True,
                "indicators": config.get("indicators", []),
            }]

        # If none explicitly marked primary, promote the first entry
        if not any(c.get("primary", False) for c in raw):
            raw[0]["primary"] = True

        specs = [
            ContextSpec(
                symbol=c["symbol"],
                timeframe=c["timeframe"],
                indicator_pipeline=IndicatorPipeline.from_config(c.get("indicators", [])),
                is_primary=c.get("primary", False),
            )
            for c in raw
        ]
        return cls(strategy, specs)

    def step(
        self,
        bars_map: dict[tuple[str, str], pd.DataFrame],
    ) -> tuple[MarketBundle, StrategySignal]:
        """
        Run one pipeline step.

        bars_map must contain a DataFrame for every (symbol, timeframe) declared
        in context_specs. Each DataFrame is independently enriched by its own
        IndicatorPipeline, then assembled into a MarketBundle and passed to the
        strategy.
        """
        contexts: dict[tuple[str, str], MarketContext] = {}
        primary_context: MarketContext | None = None

        for spec in self._specs:
            key = (spec.symbol, spec.timeframe)
            if key not in bars_map:
                raise KeyError(
                    f"bars_map is missing an entry for {key}. "
                    f"Expected keys: {[( s.symbol, s.timeframe) for s in self._specs]}"
                )
            enriched, indicator_cols = spec.indicator_pipeline.apply(bars_map[key])
            ctx = build_context(spec.symbol, spec.timeframe, enriched, indicator_cols)
            contexts[key] = ctx
            if spec.is_primary:
                primary_context = ctx

        assert primary_context is not None  # guaranteed by __init__ validation
        bundle = MarketBundle(primary=primary_context, contexts=contexts)
        signal = self.strategy.evaluate(bundle)
        return bundle, signal
