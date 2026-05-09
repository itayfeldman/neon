import pytest

from neon.lib.fixed_income.bond import Bond
from neon.lib.fixed_income.frn import FloatingRateNote

ISSUE = "20250101"
MATURITY = "20300101"
SETTLE = "20250101"


def _frn(reference_rate: float = 0.04, spread: float = 0.01) -> FloatingRateNote:
    return FloatingRateNote(
        issue_date=ISSUE,
        maturity_date=MATURITY,
        reference_rate=reference_rate,
        spread=spread,
    )


class TestFloatingRateNote:
    def test_is_bond(self):
        assert isinstance(_frn(), Bond)

    def test_coupon_rate_equals_reference_plus_spread(self):
        frn = _frn(reference_rate=0.04, spread=0.01)
        assert frn.clean_price_from_ytm(SETTLE, 0.05) == pytest.approx(100.0, abs=0.01)

    def test_higher_spread_higher_price(self):
        low = _frn(reference_rate=0.04, spread=0.005)
        high = _frn(reference_rate=0.04, spread=0.02)
        ytm = 0.05
        assert high.dirty_price_from_ytm(SETTLE, ytm) > low.dirty_price_from_ytm(
            SETTLE, ytm
        )

    def test_higher_reference_rate_higher_price(self):
        low = _frn(reference_rate=0.02, spread=0.01)
        high = _frn(reference_rate=0.05, spread=0.01)
        ytm = 0.05
        assert high.dirty_price_from_ytm(SETTLE, ytm) > low.dirty_price_from_ytm(
            SETTLE, ytm
        )

    def test_ytm_roundtrip(self):
        frn = _frn()
        ytm = 0.05
        clean = frn.clean_price_from_ytm(SETTLE, ytm)
        assert frn.yield_to_maturity(SETTLE, clean) == pytest.approx(ytm, abs=1e-6)

    def test_par_when_coupon_equals_ytm(self):
        frn = _frn(reference_rate=0.04, spread=0.01)  # coupon_rate = 0.05
        assert frn.clean_price_from_ytm(SETTLE, 0.05) == pytest.approx(
            100.0, abs=0.01
        )
