from abc import ABC

from neon.lib.datetime import time_to_maturity
from neon.lib.greeks.greeks import Greeks
from neon.lib.instruments.instrument import Instrument
from neon.lib.instruments.options.option_inputs import OptionInputs


def serialize_option_inputs(option_inputs: OptionInputs) -> str:
    """Serialize option inputs to a string for caching."""
    ticker = option_inputs.underlying_ticker
    expiry = option_inputs.expiry_date
    opt = option_inputs.option_type.name
    strike = f"{option_inputs.strike_price:.0f}"
    return f"{ticker}_{expiry}_{opt}_{strike}"


class BaseOption(Instrument, ABC):

    def __init__(self, option_inputs: OptionInputs, greeks: Greeks = Greeks()):
        super().__init__(
            ticker=serialize_option_inputs(option_inputs),
            currency=option_inputs.currency,
            multiplier=option_inputs.multiplier,
            greeks=greeks,
        )
        self.underlying_price = option_inputs.underlying_price
        self.strike_price = option_inputs.strike_price
        self.volatility = option_inputs.volatility
        self.risk_free_rate = option_inputs.risk_free_rate
        self.current_date = option_inputs.current_date
        self.expiry_date = option_inputs.expiry_date
        self.option_type = option_inputs.option_type
        self.day_count = option_inputs.day_count
        self.time_to_maturity = time_to_maturity(
            self.current_date, self.expiry_date, self.day_count
        )
