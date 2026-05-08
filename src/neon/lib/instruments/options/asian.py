import numpy as np

from neon.lib.core.constants import N_SIM
from neon.lib.core.time_steps import TimeSteps
from neon.lib.instruments.options.base import BaseOption
from neon.lib.instruments.options.option_inputs import OptionInputs
from neon.lib.pricing.monte_carlo import price_mc, simulate_gbm


class AsianOption(BaseOption):
    def __init__(
        self,
        inputs: OptionInputs,
        n_sim: int = N_SIM,
        steps: int = TimeSteps.Daily,
    ):
        super().__init__(inputs)
        self._n_sim = n_sim
        self._steps = steps

    def price(self) -> float:
        S = self.underlying_price
        K = self.strike_price
        r = self.risk_free_rate
        sigma = self.volatility
        T = self.time_to_maturity
        phi = int(self.option_type)

        paths = simulate_gbm(S, r, sigma, T, self._steps, self._n_sim)
        avg = paths[:, 1:].mean(axis=1)
        return price_mc(paths, lambda p: np.maximum(phi * (avg - K), 0.0), r, T)
