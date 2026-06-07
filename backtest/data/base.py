from __future__ import annotations

from abc import ABC, abstractmethod

import pandas as pd


class HistoricalDataSource(ABC):
    @abstractmethod
    def load_bars(
        self,
        symbol: str,
        timeframe: str,
        start: str | None = None,
        end: str | None = None,
    ) -> pd.DataFrame:
        raise NotImplementedError
