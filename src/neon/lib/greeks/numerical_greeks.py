from typing import Callable

from .greeks import Greeks


class NumericalGreeks(Greeks):
    """Computes Greeks via central finite differences on an injected pricing function.

    The pricing function must accept keyword arguments:
        underlying_price, strike_price, volatility,
        risk_free_rate, time_to_maturity, option_type
    and return a float price.
    """

    def __init__(
        self,
        pricing_fn: Callable[..., float],
        spot_bump: float = 0.01,
        vol_bump: float = 0.01,
        rate_bump: float = 0.0001,
        time_bump: float = 1 / 365,
    ) -> None:
        self.pricing_fn = pricing_fn
        self.spot_bump = spot_bump
        self.vol_bump = vol_bump
        self.rate_bump = rate_bump
        self.time_bump = time_bump

    def _reprice(self, **overrides: float) -> float:
        params = {
            "underlying_price": self.underlying_price,
            "strike_price": self.strike_price,
            "volatility": self.volatility,
            "risk_free_rate": self.risk_free_rate,
            "time_to_maturity": self.time_to_maturity,
            "option_type": self.option_type,
        }
        params.update(overrides)
        return self.pricing_fn(**params)

    def price(self) -> float:
        return self._reprice()

    def delta(self) -> float:
        h = self.spot_bump * self.underlying_price
        return (
            self._reprice(underlying_price=self.underlying_price + h)
            - self._reprice(underlying_price=self.underlying_price - h)
        ) / (2 * h)

    def gamma(self) -> float:
        h = self.spot_bump * self.underlying_price
        return (
            self._reprice(underlying_price=self.underlying_price + h)
            - 2 * self._reprice()
            + self._reprice(underlying_price=self.underlying_price - h)
        ) / (h**2)

    def vega(self) -> float:
        h = self.vol_bump
        return (
            self._reprice(volatility=self.volatility + h)
            - self._reprice(volatility=self.volatility - h)
        ) / (2 * h)

    def theta(self) -> float:
        h = self.time_bump
        return -(
            self._reprice(time_to_maturity=self.time_to_maturity + h)
            - self._reprice(time_to_maturity=self.time_to_maturity - h)
        ) / (2 * h)

    def rho(self) -> float:
        h = self.rate_bump
        return (
            self._reprice(risk_free_rate=self.risk_free_rate + h)
            - self._reprice(risk_free_rate=self.risk_free_rate - h)
        ) / (2 * h)

    def vanna(self) -> float:
        hs = self.spot_bump * self.underlying_price
        hv = self.vol_bump
        return (
            self._reprice(
                underlying_price=self.underlying_price + hs,
                volatility=self.volatility + hv,
            )
            - self._reprice(
                underlying_price=self.underlying_price + hs,
                volatility=self.volatility - hv,
            )
            - self._reprice(
                underlying_price=self.underlying_price - hs,
                volatility=self.volatility + hv,
            )
            + self._reprice(
                underlying_price=self.underlying_price - hs,
                volatility=self.volatility - hv,
            )
        ) / (4 * hs * hv)

    def volga(self) -> float:
        h = self.vol_bump
        return (
            self._reprice(volatility=self.volatility + h)
            - 2 * self._reprice()
            + self._reprice(volatility=self.volatility - h)
        ) / (h**2)
