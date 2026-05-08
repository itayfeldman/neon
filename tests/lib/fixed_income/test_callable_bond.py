import pytest

from neon.lib.fixed_income.bond import Bond
from neon.lib.fixed_income.callable_bond import CallableBond
from neon.lib.fixed_income.discount_curve import DiscountCurve

ISSUE = "20250101"
MATURITY = "20300101"
SETTLE = "20250101"
CALL_START = "20270101"  # callable from year 2 onward


def _curve(rate: float = 0.05) -> DiscountCurve:
    dates = [
        "20250701", "20260101", "20260701", "20270101",
        "20270701", "20280101", "20280701", "20290101",
        "20290701", "20300101",
    ]
    return DiscountCurve(ISSUE, dates, [rate] * len(dates))


def _bond(coupon_rate: float = 0.05, vol: float = 0.01) -> CallableBond:
    return CallableBond(
        issue_date=ISSUE,
        maturity_date=MATURITY,
        coupon_rate=coupon_rate,
        call_start=CALL_START,
        vol=vol,
        coupon_freq=2,
    )


class TestCallableBond:
    def test_is_bond(self):
        assert isinstance(_bond(), Bond)

    def test_dirty_price_returns_float(self):
        assert isinstance(_bond().dirty_price_from_tree(SETTLE, _curve()), float)

    def test_dirty_price_positive(self):
        assert _bond().dirty_price_from_tree(SETTLE, _curve()) > 0

    def test_dirty_price_below_straight_bond(self):
        # Callable bond must be cheaper than equivalent non-callable bond
        cb = _bond(vol=0.01)
        straight = Bond(ISSUE, MATURITY, 0.05, coupon_freq=2)
        curve = _curve()
        callable_price = cb.dirty_price_from_tree(SETTLE, curve)
        straight_price = straight.dirty_price_from_curve(SETTLE, curve)
        assert callable_price < straight_price

    def test_zero_vol_approaches_straight_bond(self):
        # With zero vol (flat tree), callable bond price ≈ min(straight, call price)
        # At least it should be <= straight bond price
        cb = CallableBond(ISSUE, MATURITY, 0.05, CALL_START, vol=1e-6, coupon_freq=2)
        straight = Bond(ISSUE, MATURITY, 0.05, coupon_freq=2)
        curve = _curve()
        straight_price = straight.dirty_price_from_curve(SETTLE, curve)
        assert cb.dirty_price_from_tree(SETTLE, curve) <= straight_price + 0.01

    def test_higher_vol_lower_price(self):
        # More vol → more optionality for issuer → lower price for holder
        curve = _curve()
        low_vol = _bond(vol=0.005).dirty_price_from_tree(SETTLE, curve)
        high_vol = _bond(vol=0.02).dirty_price_from_tree(SETTLE, curve)
        assert high_vol < low_vol

    def test_clean_price_from_tree(self):
        cb = _bond()
        curve = _curve()
        dirty = cb.dirty_price_from_tree(SETTLE, curve)
        accrued = cb.accrued_interest(SETTLE)
        assert cb.clean_price_from_tree(SETTLE, curve) == pytest.approx(
            dirty - accrued, abs=1e-6
        )

    def test_coupon_above_market_makes_call_likely(self):
        # High coupon → issuer very likely to call → price near face
        cb = CallableBond(ISSUE, MATURITY, 0.15, CALL_START, vol=0.01, coupon_freq=2)
        curve = _curve(rate=0.03)  # low rate → bond is deep in-the-money for issuer
        price = cb.dirty_price_from_tree(SETTLE, curve)
        # Price should be pulled toward par (100) by call option
        assert price < 130  # without call at 15% coupon it would be far above par
