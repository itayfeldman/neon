import numpy as np
from scipy.stats import norm

from .greeks import Greeks


class AnalyticalGreeks(Greeks):

    @property
    def _a_(self):
        return self.volatility * self.time_to_maturity**0.5

    @property
    def _b_(self):
        return np.exp(-self.risk_free_rate * self.time_to_maturity)

    @property
    def d1(self):
        return (
            np.log(self.underlying_price / self.strike_price)
            + (self.risk_free_rate + self.volatility**2 / 2) * self.time_to_maturity
        ) / self._a_

    @property
    def d2(self):
        return self.d1 - self._a_

    def price(self) -> float:
        return float(
            self.option_type
            * (
                self.underlying_price * norm.cdf(self.option_type * self.d1)
                - self.strike_price * self._b_ * norm.cdf(self.option_type * self.d2)
            )
        )

    def delta(self) -> float:
        return float(self.option_type * norm.cdf(self.option_type * self.d1))

    def gamma(self) -> float:
        return float(norm.pdf(self.d1) / (self.underlying_price * self._a_))

    def vega(self) -> float:
        return float(
            self.underlying_price * norm.pdf(self.d1) * self.time_to_maturity**0.5
        )

    def theta(self) -> float:
        return float(
            -(self.underlying_price * norm.pdf(self.d1) * self.volatility)
            / (2 * self.time_to_maturity**0.5)
            - self.option_type
            * self.risk_free_rate
            * self.strike_price
            * np.exp(-self.risk_free_rate * self.time_to_maturity)
            * norm.cdf(self.option_type * self.d2)
        )

    def rho(self) -> float:
        return float(
            self.option_type
            * self.strike_price
            * self.time_to_maturity
            * np.exp(-self.risk_free_rate * self.time_to_maturity)
            * norm.cdf(self.option_type * self.d2)
        )
