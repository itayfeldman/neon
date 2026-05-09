from scipy.optimize import brentq

from neon.lib.datetime.day_count import DayCount
from neon.lib.datetime.ttm import time_to_maturity
from neon.lib.fixed_income.bond import Bond

_NOTIONAL_YIELD = 0.06


class BondFuture:
    def __init__(
        self,
        delivery_date: str,
        repo_rate: float,
        notional_yield: float = _NOTIONAL_YIELD,
        day_count: DayCount = DayCount.ACT365,
    ) -> None:
        self._delivery_date = delivery_date
        self._repo_rate = repo_rate
        self._notional_yield = notional_yield
        self._day_count = day_count

    def _bond_face(self, bond: Bond) -> float:
        for attr in ("face", "notional"):
            value = getattr(bond, attr, None)
            if value is None:
                continue
            return float(value() if callable(value) else value)
        return float(getattr(bond, "_face"))

    def conversion_factor(self, bond: Bond, settle_date: str) -> float:
        clean = bond.clean_price_from_ytm(settle_date, self._notional_yield)
        return float(clean / self._bond_face(bond))

    def theoretical_price(
        self, bond: Bond, settle_date: str, clean_price: float
    ) -> float:
        T = time_to_maturity(settle_date, self._delivery_date, self._day_count)
        accrued = bond.accrued_interest(settle_date)
        carry = (clean_price + accrued) * (1 + self._repo_rate * T)

        # Subtract future value of coupons paid between settle and delivery
        coupon_fv = sum(
            bond._coupon() * (1 + self._repo_rate * time_to_maturity(
                d, self._delivery_date, self._day_count
            ))
            for d in bond._schedule.payment_dates
            if settle_date < d <= self._delivery_date
        )

        cf = self.conversion_factor(bond, self._delivery_date)
        return float((carry - coupon_fv) / cf)

    def implied_repo(
        self,
        bond: Bond,
        settle_date: str,
        clean_price: float,
        futures_price: float,
    ) -> float:
        def objective(repo: float) -> float:
            fut = BondFuture(
                self._delivery_date, repo, self._notional_yield, self._day_count
            )
            return fut.theoretical_price(bond, settle_date, clean_price) - futures_price

        return float(brentq(objective, -0.5, 2.0))

    def ctd(
        self,
        basket: list[Bond],
        settle_date: str,
        clean_prices: dict[Bond, float],
    ) -> Bond:
        futures_prices = {
            b: self.theoretical_price(b, settle_date, clean_prices[b]) for b in basket
        }
        return min(
            basket,
            key=lambda b: clean_prices[b]
            - futures_prices[b] * self.conversion_factor(b, self._delivery_date),
        )
