from neon.lib.greeks import Greeks
from neon.lib.instruments.options.base import BaseOption
from neon.lib.instruments.options.option_inputs import OptionInputs


class EuropeanOption(BaseOption):

    def __init__(self, option_inputs: OptionInputs, greeks: Greeks):
        super().__init__(option_inputs, greeks)
        greeks.underlying_price = option_inputs.underlying_price
        greeks.strike_price = option_inputs.strike_price
        greeks.volatility = option_inputs.volatility
        greeks.risk_free_rate = option_inputs.risk_free_rate
        greeks.time_to_maturity = self.time_to_maturity
        greeks.option_type = option_inputs.option_type

    def price(self) -> float:
        return self.greeks.price()

    def delta(self) -> float:
        return self.greeks.delta()

    def gamma(self) -> float:
        return self.greeks.gamma()

    def vega(self) -> float:
        return self.greeks.vega()

    def theta(self) -> float:
        return self.greeks.theta()

    def rho(self) -> float:
        return self.greeks.rho()
