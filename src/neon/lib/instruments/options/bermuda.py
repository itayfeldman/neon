import numpy as np

from neon.lib.core.time_steps import TimeSteps
from neon.lib.datetime import time_to_maturity
from neon.lib.instruments.options.base import BaseOption
from neon.lib.instruments.options.option_inputs import OptionInputs


class BermudaOption(BaseOption):
    def __init__(
        self,
        inputs: OptionInputs,
        exercise_dates: list[str],
        steps: int = TimeSteps.Daily,
    ):
        super().__init__(inputs)
        self._exercise_dates = exercise_dates
        self._steps = steps

    def price(self) -> float:
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

        exercise_steps = {
            round(time_to_maturity(self.current_date, ed, self.day_count) / dt)
            for ed in self._exercise_dates
        }

        j = np.arange(n + 1)
        ST = S * (u ** (n - j)) * (d**j)
        values = np.maximum(phi * (ST - K), 0.0)

        for step in range(n - 1, -1, -1):
            j = np.arange(step + 1)
            ST = S * (u ** (step - j)) * (d**j)
            continuation = discount * (p * values[:-1] + (1 - p) * values[1:])
            if step in exercise_steps:
                intrinsic = np.maximum(phi * (ST - K), 0.0)
                values = np.maximum(continuation, intrinsic)
            else:
                values = continuation

        return float(values[0])
