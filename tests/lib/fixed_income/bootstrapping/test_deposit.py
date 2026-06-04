import math

import pytest

from neon.lib.fixed_income.bootstrapping.deposit import Deposit
from neon.lib.fixed_income.discount_curve import DiscountCurve

VALUE_DATE = "20250101"
MATURITY = "20250701"  # ~6 months


def _curve() -> DiscountCurve:
    return DiscountCurve(VALUE_DATE, [MATURITY], [0.05])


def _deposit(rate: float = 0.05) -> Deposit:
    return Deposit(value_date=VALUE_DATE, maturity_date=MATURITY, rate=rate)


class TestDeposit:
    def test_returns_maturity_date(self):
        date, _ = _deposit().discount_factor(_curve())
        assert date == MATURITY

    def test_df_less_than_one(self):
        _, df = _deposit(rate=0.05).discount_factor(_curve())
        assert df < 1.0

    def test_df_formula(self):
        rate = 0.05
        deposit = Deposit(value_date=VALUE_DATE, maturity_date=MATURITY, rate=rate)
        _, df = deposit.discount_factor(_curve())
        # ACT/360: days between dates / 360
        t = (181) / 360  # 2025-01-01 to 2025-07-01 = 181 days
        expected = 1 / (1 + rate * t)
        assert df == pytest.approx(expected, rel=1e-6)

    def test_longer_maturity_lower_df(self):
        short = Deposit(VALUE_DATE, "20250401", rate=0.05)
        long_ = Deposit(VALUE_DATE, "20260101", rate=0.05)
        curve = DiscountCurve(VALUE_DATE, ["20260101"], [0.05])
        _, df_short = short.discount_factor(curve)
        _, df_long = long_.discount_factor(curve)
        assert df_long < df_short

    def test_zero_rate_roundtrip(self):
        _, df = _deposit(rate=0.05).discount_factor(_curve())
        # DiscountCurve uses ACT365 internally; use same denominator for implied zero
        t_act365 = 181 / 365
        implied_zero = -math.log(df) / t_act365
        curve = DiscountCurve(VALUE_DATE, [MATURITY], [implied_zero])
        assert curve.df(MATURITY) == pytest.approx(df, rel=1e-8)
