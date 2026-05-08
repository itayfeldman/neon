import math

import pytest

from neon.lib.fixed_income.discount_curve import DiscountCurve


def _curve() -> DiscountCurve:
    return DiscountCurve(
        value_date="20250101",
        dates=["20260101", "20280101", "20300101", "20350101"],
        zero_rates=[0.03, 0.035, 0.04, 0.045],
    )


class TestDf:
    def test_value_date_is_one(self):
        assert _curve().df("20250101") == pytest.approx(1.0, abs=1e-10)

    def test_returns_float(self):
        assert isinstance(_curve().df("20260101"), float)

    def test_knot_point(self):
        curve = _curve()
        t = (365) / 365  # ~1 year
        expected = math.exp(-0.03 * t)
        assert curve.df("20260101") == pytest.approx(expected, rel=1e-4)

    def test_monotonically_decreasing(self):
        curve = _curve()
        dfs = [curve.df(d) for d in ["20260101", "20280101", "20300101", "20350101"]]
        assert dfs == sorted(dfs, reverse=True)

    def test_clamped_beyond_last_date(self):
        result = _curve().df("20500101")
        assert isinstance(result, float)
        assert result > 0


class TestZeroRate:
    def test_roundtrip_with_df(self):
        curve = _curve()
        for date in ["20260101", "20280101", "20300101"]:
            df = curve.df(date)
            r = curve.zero_rate(date)
            t = curve._years_from_value(date)
            assert math.exp(-r * t) == pytest.approx(df, rel=1e-10)

    def test_returns_float(self):
        assert isinstance(_curve().zero_rate("20280101"), float)


class TestForwardRate:
    def test_returns_float(self):
        assert isinstance(_curve().forward_rate("20260101", "20280101"), float)

    def test_positive_for_upward_curve(self):
        assert _curve().forward_rate("20260101", "20280101") > 0

    def test_consistent_with_dfs(self):
        curve = _curve()
        d1, d2 = "20260101", "20280101"
        df1 = curve.df(d1)
        df2 = curve.df(d2)
        t1 = curve._years_from_value(d1)
        t2 = curve._years_from_value(d2)
        expected = (math.log(df1) - math.log(df2)) / (t2 - t1)
        assert curve.forward_rate(d1, d2) == pytest.approx(expected, rel=1e-6)
