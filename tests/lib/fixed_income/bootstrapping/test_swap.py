import pytest

from neon.lib.fixed_income.bootstrapping.swap import Swap
from neon.lib.fixed_income.discount_curve import DiscountCurve

VALUE_DATE = "20250101"


def _flat_curve(rate: float = 0.05) -> DiscountCurve:
    dates = ["20250701", "20260101", "20270101", "20280101", "20300101"]
    return DiscountCurve(VALUE_DATE, dates, [rate] * len(dates))


class TestSwap:
    def test_returns_maturity_date(self):
        swap = Swap(VALUE_DATE, "20270101", fixed_rate=0.05)
        date, _ = swap.discount_factor(_flat_curve())
        assert date == "20270101"

    def test_df_less_than_one(self):
        swap = Swap(VALUE_DATE, "20270101", fixed_rate=0.05)
        _, df = swap.discount_factor(_flat_curve())
        assert df < 1.0

    def test_higher_rate_lower_df(self):
        curve = _flat_curve()
        _, df_low = Swap(VALUE_DATE, "20270101", fixed_rate=0.03).discount_factor(curve)
        _, df_high = Swap(
            VALUE_DATE, "20270101", fixed_rate=0.07
        ).discount_factor(curve)
        assert df_high < df_low

    def test_par_condition(self):
        # On a flat curve, the bootstrapped df should satisfy the par condition:
        # fixed_rate/freq * sum(df(t_i)) + df(T) = 1
        rate = 0.05
        maturity = "20270101"
        curve = _flat_curve(rate)
        swap = Swap(VALUE_DATE, maturity, fixed_rate=rate)
        _, df_T = swap.discount_factor(curve)

        # Build coupon dates (semi-annual from maturity backward)
        from neon.lib.fixed_income.coupon_schedule import CouponSchedule
        schedule = CouponSchedule(VALUE_DATE, maturity, coupon_freq=2)
        coupon_dates = schedule.payment_dates[:-1]  # exclude maturity

        # full annuity includes the maturity payment
        full_annuity = sum(curve.df(d) for d in coupon_dates) + df_T
        assert rate / 2 * full_annuity + df_T == pytest.approx(1.0, abs=1e-6)
