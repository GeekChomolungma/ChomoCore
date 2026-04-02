from __future__ import annotations

from collections.abc import Callable
from typing import Any

from quant_core.strategies.base import BaseStrategy


StrategyFactory = Callable[..., BaseStrategy]


class StrategyRegistry:
    _registry: dict[str, StrategyFactory] = {}

    @classmethod
    def register(cls, name: str) -> Callable[[StrategyFactory], StrategyFactory]:
        def decorator(factory: StrategyFactory) -> StrategyFactory:
            cls._registry[name] = factory
            return factory

        return decorator

    @classmethod
    def create(cls, name: str, **kwargs: Any) -> BaseStrategy:
        if name not in cls._registry:
            available = ", ".join(sorted(cls._registry))
            raise KeyError(f"Strategy '{name}' is not registered. Available: {available}")
        return cls._registry[name](**kwargs)

    @classmethod
    def available(cls) -> list[str]:
        return sorted(cls._registry)
