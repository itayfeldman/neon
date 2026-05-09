import pytest

from neon.lib.fixed_income.bond import Bond
from neon.lib.fixed_income.zero_coupon_bond import ZeroCouponBond

ISSUE = "20250101"
MATURITY = "20350101"
SETTLE = "20250101"
FACE = 100.0


def _zcb() -> ZeroCouponBond:
    return ZeroCouponBond(issue_date=ISSUE, maturity_date=MATURITY, face=FACE)


class TestZeroCouponBond:
    def test_is_bond(self):
        assert isinstance(_zcb(), Bond)

    def test_no_accrued_interest(self):
        assert _zcb().accrued_interest(SETTLE) == pytest.approx(0.0)

    def test_dirty_price_is_between_zero_and_face(self):
        ytm = 0.05
        zcb = _zcb()
        price = zcb.dirty_price_from_ytm(SETTLE, ytm)
        # For a positive yield on a zero-coupon bond priced at issuance,
        # the discounted redemption value should be positive and below face.
        assert 0 < price < FACE

    def test_price_increases_as_ytm_falls(self):
        zcb = _zcb()
        assert zcb.dirty_price_from_ytm(SETTLE, 0.03) > zcb.dirty_price_from_ytm(
            SETTLE, 0.07
        )

    def test_ytm_roundtrip(self):
        zcb = _zcb()
        ytm = 0.05
        clean = zcb.clean_price_from_ytm(SETTLE, ytm)
        assert zcb.yield_to_maturity(SETTLE, clean) == pytest.approx(ytm, abs=1e-6)

    def test_clean_equals_dirty_at_issue(self):
        zcb = _zcb()
        ytm = 0.05
        assert zcb.clean_price_from_ytm(SETTLE, ytm) == pytest.approx(
            zcb.dirty_price_from_ytm(SETTLE, ytm)
        )
