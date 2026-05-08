import pytest

from neon.lib.fixed_income.bootstrapping.fra import FRA
from neon.lib.fixed_income.discount_curve import DiscountCurve

VALUE_DATE = "20250101"
START = "20250701"   # 6M
END = "20260101"     # 12M


def _curve() -> DiscountCurve:
    # flat 5% curve so df(start) is well-defined
    return DiscountCurve(VALUE_DATE, [START, END], [0.05, 0.05])


def _fra(rate: float = 0.05) -> FRA:
    return FRA(start_date=START, end_date=END, rate=rate)


class TestFRA:
    def test_returns_end_date(self):
        date, _ = _fra().discount_factor(_curve())
        assert date == END

    def test_df_less_than_near_date(self):
        curve = _curve()
        _, df_end = _fra().discount_factor(curve)
        assert df_end < curve.df(START)

    def test_df_formula(self):
        curve = _curve()
        rate = 0.05
        fra = FRA(start_date=START, end_date=END, rate=rate)
        _, df_end = fra.discount_factor(curve)
        # ACT/360: 184 days from 2025-07-01 to 2026-01-01
        t = 184 / 360
        expected = curve.df(START) / (1 + rate * t)
        assert df_end == pytest.approx(expected, rel=1e-6)

    def test_higher_rate_lower_df(self):
        curve = _curve()
        _, df_low = FRA(START, END, rate=0.03).discount_factor(curve)
        _, df_high = FRA(START, END, rate=0.07).discount_factor(curve)
        assert df_high < df_low

    def test_implied_forward_rate_roundtrip(self):
        rate = 0.05
        curve = _curve()
        _, df_end = FRA(START, END, rate).discount_factor(curve)
        t = 184 / 360
        implied = (curve.df(START) / df_end - 1) / t
        assert implied == pytest.approx(rate, rel=1e-6)
