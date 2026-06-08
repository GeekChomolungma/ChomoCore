from __future__ import annotations

from dataclasses import dataclass

from core.context.market_context import MarketContext


@dataclass
class MarketBundle:
    """
    A collection of MarketContexts passed to every strategy evaluation.

    primary  — the context the resulting signal is attributed to (symbol + timeframe
               that drives the decision).
    contexts — all available contexts keyed by (symbol, timeframe). Always includes
               the primary. Multi-asset / multi-timeframe strategies look up
               additional contexts here.
    """

    primary: MarketContext
    contexts: dict[tuple[str, str], MarketContext]

    def get(self, symbol: str, timeframe: str) -> MarketContext:
        key = (symbol, timeframe)
        if key not in self.contexts:
            available = ", ".join(f"{s}/{t}" for s, t in sorted(self.contexts))
            raise KeyError(
                f"No context for ({symbol!r}, {timeframe!r}). Available: {available}"
            )
        return self.contexts[key]
