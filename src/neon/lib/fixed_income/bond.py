from scipy.optimize import brentq

from neon.lib.datetime.day_count import DayCount
from neon.lib.datetime.ttm import time_to_maturity
from neon.lib.fixed_income.coupon_schedule import CouponSchedule


class Bond:
    def __init__(
        self,
        issue_date: str,
        maturity_date: str,
        coupon_rate: float,
        coupon_freq: int = 2,
        day_count: DayCount = DayCount.ACT365,
        face: float = 100.0,
    ) -> None:
        self._issue_date = issue_date
        self._maturity_date = maturity_date
        self._coupon_rate = coupon_rate
        self._coupon_freq = coupon_freq
        self._day_count = day_count
        self._face = face
        self._schedule = CouponSchedule(issue_date, maturity_date, coupon_freq)

    def _coupon(self) -> float:
        return self._face * self._coupon_rate / self._coupon_freq

    def _future_cashflows(self, settle_date: str) -> list[tuple[str, float]]:
        coupon = self._coupon()
        cashflows = [
            (d, coupon)
            for d in self._schedule.payment_dates
            if d > settle_date
        ]
        if cashflows:
            last_date, _ = cashflows[-1]
            cashflows[-1] = (last_date, coupon + self._face)
        return cashflows

    @property
    def face(self) -> float:
        return self._face

    def future_cashflows(self, settle_date: str) -> list[tuple[str, float]]:
        return self._future_cashflows(settle_date)

    def _last_coupon_date(self, settle_date: str) -> str | None:
        past = [d for d in self._schedule.payment_dates if d <= settle_date]
        return past[-1] if past else None

    def _next_coupon_date(self, settle_date: str) -> str | None:
        future = [d for d in self._schedule.payment_dates if d > settle_date]
        return future[0] if future else None

    def _accrual_start(self, settle_date: str) -> str:
        last = self._last_coupon_date(settle_date)
        return last if last is not None else self._issue_date

    def accrued_interest(self, settle_date: str) -> float:
        start = self._accrual_start(settle_date)
        next_ = self._next_coupon_date(settle_date)
        if next_ is None:
            return 0.0
        period = time_to_maturity(start, next_, self._day_count)
        elapsed = time_to_maturity(start, settle_date, self._day_count)
        return float(self._coupon() * elapsed / period)

    def dirty_price_from_ytm(self, settle_date: str, ytm: float) -> float:
        r = ytm / self._coupon_freq
        cashflows = self._future_cashflows(settle_date)
        if not cashflows:
            return 0.0
        # Fractional first period: time from settle to next coupon in coupon periods
        next_coupon = cashflows[0][0]
        accrual_start = self._accrual_start(settle_date)
        full_period = time_to_maturity(accrual_start, next_coupon, self._day_count)
        elapsed = time_to_maturity(accrual_start, settle_date, self._day_count)
        w = (full_period - elapsed) / full_period  # fraction of first period remaining

        price = 0.0
        for i, (_, cf) in enumerate(cashflows):
            periods = w + i
            price += cf / (1 + r) ** periods
        return float(price)

    def clean_price_from_ytm(self, settle_date: str, ytm: float) -> float:
        return float(
            self.dirty_price_from_ytm(settle_date, ytm)
            - self.accrued_interest(settle_date)
        )

    def yield_to_maturity(self, settle_date: str, clean_price: float) -> float:
        dirty = clean_price + self.accrued_interest(settle_date)

        def objective(ytm: float) -> float:
            return self.dirty_price_from_ytm(settle_date, ytm) - dirty

        return float(brentq(objective, 1e-6, 10.0))

    def dirty_price_from_curve(self, settle_date: str, curve: object) -> float:
        price = sum(
            cf * curve.df(date)
            for date, cf in self._future_cashflows(settle_date)
        )
        return float(price)
