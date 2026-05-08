import pytest

from neon.lib.fixed_income.bond import Bond
from neon.lib.fixed_income.discount_curve import DiscountCurve


def _bond(coupon_rate=0.05, maturity="20350101", freq=2) -> Bond:
    return Bond(
        issue_date="20250101",
        maturity_date=maturity,
        coupon_rate=coupon_rate,
        coupon_freq=freq,
    )


class TestAccruedInterest:
    def test_zero_at_coupon_date(self):
        bond = _bond()
        # Last coupon date before settlement is 6 months prior to maturity step
        assert bond.accrued_interest("20250701") == pytest.approx(0.0, abs=1e-6)

    def test_positive_between_coupons(self):
        assert _bond().accrued_interest("20250401") > 0

    def test_returns_float(self):
        assert isinstance(_bond().accrued_interest("20250401"), float)


class TestDirtyPrice:
    def test_par_at_issuance_ytm_equals_coupon(self):
        bond = _bond(coupon_rate=0.05)
        price = bond.dirty_price_from_ytm("20250101", ytm=0.05)
        assert price == pytest.approx(100.0, abs=0.01)

    def test_premium_when_ytm_below_coupon(self):
        assert _bond().dirty_price_from_ytm("20250101", ytm=0.03) > 100.0

    def test_discount_when_ytm_above_coupon(self):
        assert _bond().dirty_price_from_ytm("20250101", ytm=0.07) < 100.0

    def test_returns_float(self):
        assert isinstance(_bond().dirty_price_from_ytm("20250101", 0.05), float)


class TestCleanPrice:
    def test_clean_equals_dirty_minus_accrued(self):
        bond = _bond()
        settle = "20250401"
        dirty = bond.dirty_price_from_ytm(settle, 0.05)
        accrued = bond.accrued_interest(settle)
        clean = bond.clean_price_from_ytm(settle, 0.05)
        assert clean == pytest.approx(dirty - accrued, abs=1e-6)

    def test_par_at_issuance(self):
        bond = _bond(coupon_rate=0.05)
        assert bond.clean_price_from_ytm("20250101", 0.05) == pytest.approx(
            100.0, abs=0.01
        )


class TestYieldToMaturity:
    def test_roundtrip(self):
        bond = _bond()
        settle = "20250401"
        ytm0 = 0.045
        clean = bond.clean_price_from_ytm(settle, ytm0)
        ytm1 = bond.yield_to_maturity(settle, clean)
        assert ytm1 == pytest.approx(ytm0, abs=1e-6)

    def test_returns_float(self):
        bond = _bond()
        assert isinstance(bond.yield_to_maturity("20250401", 99.0), float)


class TestPriceFromCurve:
    def test_flat_curve_matches_ytm_price(self):
        bond = _bond(coupon_rate=0.05)
        settle = "20250101"
        ytm = 0.05
        ytm_price = bond.dirty_price_from_ytm(settle, ytm)

        # Build flat zero curve at 5% continuously compounded
        dates = ["20260101", "20300101", "20350101", "20400101"]
        rates = [0.05] * 4
        curve = DiscountCurve(settle, dates, rates)
        curve_price = bond.dirty_price_from_curve(settle, curve)

        # Not exact (ytm is semi-annual compounding; curve is continuous)
        # but should be in the same ballpark
        assert abs(curve_price - ytm_price) < 5.0

    def test_returns_float(self):
        bond = _bond()
        curve = DiscountCurve(
            "20250101",
            ["20260101", "20350101", "20400101"],
            [0.04, 0.05, 0.05],
        )
        assert isinstance(bond.dirty_price_from_curve("20250101", curve), float)
