from datetime import datetime, timedelta

import numpy as np

from neon.lib.core.constants import DATE_FORMAT
from neon.lib.datetime.day_count import DayCount
from neon.lib.datetime.ttm import time_to_maturity
from neon.lib.fixed_income.bond import Bond

_STEPS = 100


class CallableBond(Bond):
    def __init__(
        self,
        issue_date: str,
        maturity_date: str,
        coupon_rate: float,
        call_start: str,
        vol: float,
        coupon_freq: int = 2,
        day_count: DayCount = DayCount.ACT365,
        face: float = 100.0,
    ) -> None:
        super().__init__(
            issue_date=issue_date,
            maturity_date=maturity_date,
            coupon_rate=coupon_rate,
            coupon_freq=coupon_freq,
            day_count=day_count,
            face=face,
        )
        self._call_start = call_start
        self._vol = vol

    def dirty_price_from_tree(self, settle_date: str, curve: object) -> float:
        T = time_to_maturity(settle_date, self._maturity_date, self._day_count)
        n = _STEPS
        dt = T / n
        sigma = self._vol
        coupon = self._coupon()
        face = self._face

        # Forward rates from curve: θ(i) calibrates the tree to the curve
        # r(i, j) = f(i*dt) + j * sigma * sqrt(dt)  (Ho-Lee)
        # where f(t) is the instantaneous forward rate at time t
        times = np.arange(1, n + 1) * dt
        # forward rate at each step midpoint from the curve
        fwd = np.array([curve.forward_rate(
            settle_date,
            _offset_date(settle_date, t, self._day_count)
        ) for t in times])

        # Determine which tree steps correspond to coupon and call dates
        payment_dates = self._schedule.payment_dates
        coupon_steps = set()
        call_steps = set()
        for pd in payment_dates:
            if pd <= settle_date:
                continue
            t_pd = time_to_maturity(settle_date, pd, self._day_count)
            step = min(round(t_pd / dt), n)
            coupon_steps.add(step)
            if pd >= self._call_start:
                call_steps.add(step)

        # Terminal bond values at maturity (face only; coupons are added during backward induction)
        n_nodes = n + 1
        values = np.full(n_nodes, face, dtype=float)

        # Backward induction
        for i in range(n - 1, -1, -1):
            step = i + 1  # step index of the child nodes we just computed
            r = fwd[i] + np.arange(i + 1) * sigma * np.sqrt(dt)
            discount = np.exp(-r * dt)
            # Risk-neutral probabilities (Ho-Lee: p = 0.5)
            cont = discount * 0.5 * (values[:i + 1] + values[1:i + 2])
            # Add coupon cash flow arriving at child step
            if step in coupon_steps:
                cont += coupon * discount
            # Issuer calls at par on callable steps; if the call occurs on a
            # coupon payment date, the holder also receives that coupon.
            # `cont` is a parent-node value, so the call payoff must be
            # discounted one step to be compared consistently.
            if step in call_steps:
                call_payoff = face + (coupon if step in coupon_steps else 0.0)
                cont = np.minimum(cont, call_payoff * discount)
            values = cont

        return float(values[0])

    def clean_price_from_tree(self, settle_date: str, curve: object) -> float:
        return float(
            self.dirty_price_from_tree(settle_date, curve)
            - self.accrued_interest(settle_date)
        )


def _offset_date(base: str, years: float, day_count: DayCount) -> str:
    """Return a DATE_FORMAT string approximately `years` years after base."""
    convention = getattr(day_count, "name", str(day_count)).upper()
    if "360" in convention:
        days_per_year = 360
    elif "365" in convention:
        days_per_year = 365
    else:
        days_per_year = 365

    dt = datetime.strptime(base, DATE_FORMAT) + timedelta(
        days=round(years * days_per_year)
    )
    return dt.strftime(DATE_FORMAT)
