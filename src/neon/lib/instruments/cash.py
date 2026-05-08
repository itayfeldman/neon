from neon.lib.core import Currency
from neon.lib.greeks import Greeks
from neon.lib.instruments.instrument import Instrument


class Cash(Instrument):

    def __init__(
        self,
        ticker: str = "CASH",
        currency: Currency = Currency.USD,
        multiplier: int = 1,
        greeks: Greeks = Greeks(),
    ):
        super().__init__(ticker, currency, multiplier, greeks)

    def price(self) -> float:
        return 1.0
