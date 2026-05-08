import pytest

from neon.lib.fixed_income.bootstrapping.bootstrapper import CurveBootstrapper
from neon.lib.fixed_income.bootstrapping.deposit import Deposit
from neon.lib.fixed_income.bootstrapping.fra import FRA
from neon.lib.fixed_income.bootstrapping.swap import Swap
from neon.lib.fixed_income.discount_curve import DiscountCurve

VALUE_DATE = "20250101"


class TestCurveBootstrapper:
    def test_returns_discount_curve(self):
        instruments = [Deposit(VALUE_DATE, "20260101", rate=0.05)]
        curve = CurveBootstrapper(VALUE_DATE, instruments).build()
        assert isinstance(curve, DiscountCurve)

    def test_deposit_only_zero_rate(self):
        # df from deposit formula, zero rate implied via ACT365
        rate = 0.05
        maturity = "20260101"
        instruments = [Deposit(VALUE_DATE, maturity, rate=rate)]
        curve = CurveBootstrapper(VALUE_DATE, instruments).build()

        # Expected df from simple-interest formula (ACT360: 365 days)
        t_act360 = 365 / 360
        expected_df = 1 / (1 + rate * t_act360)
        assert curve.df(maturity) == pytest.approx(expected_df, rel=1e-6)

    def test_instruments_sorted_by_maturity(self):
        # Supply out of order — bootstrapper must sort
        d6m = Deposit(VALUE_DATE, "20250701", rate=0.04)
        d3m = Deposit(VALUE_DATE, "20250401", rate=0.03)
        curve = CurveBootstrapper(VALUE_DATE, [d6m, d3m]).build()
        # Both pillars present; df is monotonically decreasing
        assert curve.df("20250401") > curve.df("20250701")

    def test_fra_chains_from_deposit(self):
        d6m = Deposit(VALUE_DATE, "20250701", rate=0.04)
        fra = FRA("20250701", "20260101", rate=0.05)
        curve = CurveBootstrapper(VALUE_DATE, [d6m, fra]).build()
        # df at 12M must be less than df at 6M
        assert curve.df("20260101") < curve.df("20250701")

    def test_swap_prices_at_par(self):
        # Annual swap (freq=1): coupon dates are 1Y and 2Y.
        # Bootstrap with deposits at 1Y and the 2Y swap so all coupon
        # dates are exact curve pillars — par must hold to numerical precision.
        rate = 0.05
        d1y = Deposit(VALUE_DATE, "20260101", rate=rate)
        swap = Swap(VALUE_DATE, "20270101", fixed_rate=rate, coupon_freq=1)
        curve = CurveBootstrapper(VALUE_DATE, [d1y, swap]).build()

        from neon.lib.fixed_income.coupon_schedule import CouponSchedule
        schedule = CouponSchedule(VALUE_DATE, "20270101", coupon_freq=1)
        annuity = sum(curve.df(d) for d in schedule.payment_dates)
        fixed_pv = rate * annuity
        float_pv = 1 - curve.df("20270101")
        assert fixed_pv == pytest.approx(float_pv, abs=1e-6)

    def test_mixed_instruments(self):
        instruments = [
            Deposit(VALUE_DATE, "20250401", rate=0.04),
            FRA("20250401", "20250701", rate=0.045),
            Swap(VALUE_DATE, "20270101", fixed_rate=0.05),
        ]
        curve = CurveBootstrapper(VALUE_DATE, instruments).build()
        assert isinstance(curve, DiscountCurve)
        # Monotonically decreasing dfs
        assert curve.df("20250401") > curve.df("20250701") > curve.df("20270101")

    def test_df_at_value_date_is_one(self):
        instruments = [Deposit(VALUE_DATE, "20260101", rate=0.05)]
        curve = CurveBootstrapper(VALUE_DATE, instruments).build()
        assert curve.df(VALUE_DATE) == pytest.approx(1.0)
