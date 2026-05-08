import numpy as np

from neon.lib.core.time_steps import TimeSteps
from neon.lib.greeks.greeks import Greeks
from neon.lib.instruments.options.base import BaseOption
from neon.lib.instruments.options.option_inputs import OptionInputs


class AmericanOption(BaseOption):
    def __init__(
        self,
        inputs: OptionInputs,
        greeks: Greeks = Greeks(),
        steps: int = TimeSteps.Daily,
    ):
        super().__init__(inputs, greeks)
        self._steps = steps

    def price(self) -> float:
        return self._crr_price()

    def _crr_price(self) -> float:
        S = self.underlying_price
        K = self.strike_price
        r = self.risk_free_rate
        sigma = self.volatility
        T = self.time_to_maturity
        phi = int(self.option_type)
        n = self._steps

        dt = T / n
        u = np.exp(sigma * np.sqrt(dt))
        d = 1.0 / u
        p = (np.exp(r * dt) - d) / (u - d)
        discount = np.exp(-r * dt)

        # Terminal stock prices and payoffs
        j = np.arange(n + 1)
        ST = S * (u ** (n - j)) * (d**j)
        values = np.maximum(phi * (ST - K), 0.0)

        # Backward induction with early exercise
        for _ in range(n):
            j = np.arange(len(values) - 1)
            ST = S * (u ** (len(values) - 2 - j)) * (d**j)
            continuation = discount * (p * values[:-1] + (1 - p) * values[1:])
            intrinsic = np.maximum(phi * (ST - K), 0.0)
            values = np.maximum(continuation, intrinsic)

        return float(values[0])
