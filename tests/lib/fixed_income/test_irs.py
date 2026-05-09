import pytest

from neon.lib.fixed_income.discount_curve import DiscountCurve
from neon.lib.fixed_income.irs import InterestRateSwap

VALUE_DATE = "20250101"
MATURITY = "20270101"
NOTIONAL = 1_000_000.0
RATE = 0.05


def _flat_curve(rate: float = RATE) -> DiscountCurve:
    dates = ["20250701", "20260101", "20260701", "20270101"]
    return DiscountCurve(VALUE_DATE, dates, [rate] * len(dates))


def _swap(fixed_rate: float = RATE) -> InterestRateSwap:
    return InterestRateSwap(
        value_date=VALUE_DATE,
        maturity_date=MATURITY,
        fixed_rate=fixed_rate,
        notional=NOTIONAL,
    )


class TestFixedLegPV:
    def test_returns_float(self):
        assert isinstance(_swap().fixed_leg_pv(_flat_curve()), float)

    def test_positive(self):
        assert _swap().fixed_leg_pv(_flat_curve()) > 0

    def test_higher_rate_higher_fixed_pv(self):
        curve = _flat_curve()
        assert _swap(0.07).fixed_leg_pv(curve) > _swap(0.03).fixed_leg_pv(curve)


class TestFloatLegPV:
    def test_returns_float(self):
        assert isinstance(_swap().float_leg_pv(VALUE_DATE, _flat_curve()), float)

    def test_positive(self):
        assert _swap().float_leg_pv(VALUE_DATE, _flat_curve()) > 0

    def test_equals_notional_times_df_difference(self):
        curve = _flat_curve()
        pv = _swap().float_leg_pv(VALUE_DATE, curve)
        expected = NOTIONAL * (curve.df(VALUE_DATE) - curve.df(MATURITY))
        assert pv == pytest.approx(expected, rel=1e-6)


class TestPV:
    def test_returns_float(self):
        assert isinstance(_swap().pv(VALUE_DATE, _flat_curve()), float)

    def test_pv_equals_fixed_minus_float(self):
        curve = _flat_curve()
        swap = _swap()
        assert swap.pv(VALUE_DATE, curve) == pytest.approx(
            swap.fixed_leg_pv(curve) - swap.float_leg_pv(VALUE_DATE, curve),
            rel=1e-6,
        )

    def test_at_par_rate_pv_is_zero(self):
        swap = _swap()
        curve = _flat_curve()
        par = swap.par_rate(VALUE_DATE, curve)
        at_par = InterestRateSwap(VALUE_DATE, MATURITY, par, NOTIONAL)
        assert at_par.pv(VALUE_DATE, curve) == pytest.approx(0.0, abs=1e-4)


class TestParRate:
    def test_returns_float(self):
        assert isinstance(_swap().par_rate(VALUE_DATE, _flat_curve()), float)

    def test_positive(self):
        assert _swap().par_rate(VALUE_DATE, _flat_curve()) > 0

    def test_flat_curve_par_rate_near_zero_rate(self):
        # On a flat continuously-compounded curve, par rate ≈ (1 - df(T)) / annuity
        rate = 0.05
        curve = _flat_curve(rate)
        par = _swap().par_rate(VALUE_DATE, curve)
        # par rate should be close to the flat zero rate
        assert par == pytest.approx(rate, abs=0.01)


class TestDV01:
    def test_returns_float(self):
        assert isinstance(_swap().dv01(VALUE_DATE, _flat_curve()), float)

    def test_receiver_swap_positive_dv01(self):
        # Receiver swap (long fixed): price rises when rates fall → dv01 > 0
        assert _swap().dv01(VALUE_DATE, _flat_curve()) > 0

    def test_longer_maturity_higher_dv01(self):
        curve = _flat_curve()
        short = InterestRateSwap(VALUE_DATE, "20260101", RATE, NOTIONAL)
        long_ = InterestRateSwap(VALUE_DATE, "20280101", RATE, NOTIONAL)
        dates_ext = [
            "20250701", "20260101", "20260701", "20270101", "20270701", "20280101"
        ]
        curve_ext = DiscountCurve(VALUE_DATE, dates_ext, [RATE] * len(dates_ext))
        assert long_.dv01(VALUE_DATE, curve_ext) > short.dv01(VALUE_DATE, curve)
