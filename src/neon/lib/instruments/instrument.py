from abc import ABC, abstractmethod
from dataclasses import dataclass

from neon.lib.core import Currency
from neon.lib.greeks import Greeks


@dataclass
class Instrument(ABC):
    """Base class for financial instruments."""

    ticker: str
    currency: Currency
    multiplier: int
    greeks: Greeks

    @abstractmethod
    def price(self) -> float:
        """Calculate the price of the instrument."""
        pass
