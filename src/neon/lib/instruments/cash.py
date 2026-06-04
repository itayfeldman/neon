from dataclasses import dataclass

from neon.lib.core import Currency
from neon.lib.greeks import Greeks
from neon.lib.instruments.instrument import Instrument


@dataclass(frozen=True, slots=True)
class Cash(Instrument):
    ticker: str = "CASH"
    currency: Currency = Currency.USD
    multiplier: int = 1
    greeks: Greeks = Greeks()

    def price(self) -> float:
        return 1.0
