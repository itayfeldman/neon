from typing import Protocol

from neon.lib.core import Currency
from neon.lib.greeks import Greeks


class Instrument(Protocol):
    ticker: str = ""
    currency: Currency = Currency.USD
    multiplier: int = 1
    greeks: Greeks = Greeks()

    def price(self) -> float:
        """Calculate the price of the instrument."""
        raise NotImplementedError(f"Price method must be implemented by {self.__class__.__name__}.")