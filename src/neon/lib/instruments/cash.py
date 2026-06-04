from dataclasses import dataclass, field

from neon.lib.core import Currency
from neon.lib.greeks import Greeks
from neon.lib.instruments.instrument import Instrument


@dataclass(slots=True)
class Cash(Instrument):
    ticker: str = "CASH"
    currency: Currency = Currency.USD
    multiplier: int = 1
    greeks: Greeks = field(default_factory=Greeks)

    def price(self) -> float:
        return 1.0
