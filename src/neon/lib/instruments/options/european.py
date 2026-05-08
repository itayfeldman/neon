from neon.lib.instruments.options.base import BaseOption
from neon.lib.instruments.options.option_inputs import OptionInputs
from neon.lib.greeks import Greeks


class EuropeanOption(BaseOption):

    def __init__(self, option_inputs: OptionInputs, greeks: Greeks):
        super().__init__(option_inputs)
        self.greeks: Greeks = greeks

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
