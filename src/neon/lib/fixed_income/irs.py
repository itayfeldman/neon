from neon.lib.datetime.day_count import DayCount
from neon.lib.fixed_income.coupon_schedule import CouponSchedule
from neon.lib.fixed_income.discount_curve import DiscountCurve

_BP = 0.0001


class InterestRateSwap:
    def __init__(
        self,
        value_date: str,
        maturity_date: str,
        fixed_rate: float,
        notional: float = 1_000_000.0,
        coupon_freq: int = 2,
        day_count: DayCount = DayCount.ACT365,
    ) -> None:
        self._value_date = value_date
        self._maturity_date = maturity_date
        self._fixed_rate = fixed_rate
        self._notional = notional
        self._coupon_freq = coupon_freq
        self._day_count = day_count
        self._schedule = CouponSchedule(value_date, maturity_date, coupon_freq)

    def fixed_leg_pv(self, curve: object) -> float:
        c = self._fixed_rate / self._coupon_freq * self._notional
        return float(sum(c * curve.df(d) for d in self._schedule.payment_dates))

    def float_leg_pv(self, settle_date: str, curve: object) -> float:
        return float(
            self._notional * (curve.df(settle_date) - curve.df(self._maturity_date))
        )

    def pv(self, settle_date: str, curve: object) -> float:
        """PV from receiver perspective: positive when fixed_leg > float_leg."""
        return float(self.fixed_leg_pv(curve) - self.float_leg_pv(settle_date, curve))

    def par_rate(self, settle_date: str, curve: object) -> float:
        annuity = sum(curve.df(d) for d in self._schedule.payment_dates)
        return float(
            self._coupon_freq
            * (curve.df(settle_date) - curve.df(self._maturity_date))
            / annuity
        )

    def dv01(self, settle_date: str, curve: DiscountCurve) -> float:
        pv_up = self._shifted_pv(settle_date, curve, +_BP)
        pv_dn = self._shifted_pv(settle_date, curve, -_BP)
        return float((pv_dn - pv_up) / 2)

    def _shifted_pv(
        self, settle_date: str, curve: DiscountCurve, shift: float
    ) -> float:
        if not all(
            hasattr(curve, attr) for attr in ("value_date", "dates", "zero_rates")
        ):
            raise TypeError(
                "curve must provide value_date, dates, and zero_rates for dv01"
            )
        shifted = DiscountCurve(
            curve.value_date,
            curve.dates,
            [r + shift for r in curve.zero_rates],
        )
        return self.pv(settle_date, shifted)
