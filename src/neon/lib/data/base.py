from abc import ABC, abstractmethod
from typing import Any

import pandas as pd


class DataFetchError(Exception):
    pass


class DataAdapter(ABC):
    @abstractmethod
    def fetch(self, **kwargs) -> pd.DataFrame:
        pass

    @abstractmethod
    def to_domain(self, df: pd.DataFrame) -> Any:
        pass
