import pytest

from neon.lib.core.currency import Currency
from neon.lib.fixed_income.bond import Bond
from neon.lib.instruments.cash import Cash
from neon.lib.portfolio.portfolio import Portfolio
from neon.lib.portfolio.position import Position
from neon.lib.risk.risk_engine import RiskEngine

_SETTLE = "20250101"
_YTM = 0.05


def _bond(coupon: float = 0.05, maturity: str = "20350101") -> Bond:
    return Bond(
        issue_date=_SETTLE,
        maturity_date=maturity,
        coupon_rate=coupon,
        coupon_freq=2,
    )


def _engine(bond: Bond, qty: float = 1.0) -> RiskEngine:
    p = Portfolio(name="test")
    p.add_position(Position(instrument=bond, quantity=qty))
    return RiskEngine(p)


class TestBondRisk:
    def test_dv01_returns_float(self):
        b = _bond()
        result = _engine(b).bond_risk(_SETTLE, {b: _YTM})
        assert isinstance(result.dv01, float)

    def test_dv01_positive_for_long(self):
        b = _bond()
        result = _engine(b, qty=1.0).bond_risk(_SETTLE, {b: _YTM})
        assert result.dv01 > 0

    def test_dv01_scales_with_quantity(self):
        b = _bond()
        r1 = _engine(b, qty=1.0).bond_risk(_SETTLE, {b: _YTM})
        r2 = _engine(b, qty=2.0).bond_risk(_SETTLE, {b: _YTM})
        assert r2.dv01 == pytest.approx(2 * r1.dv01, rel=1e-6)

    def test_dv01_short_negative(self):
        b = _bond()
        result = _engine(b, qty=-1.0).bond_risk(_SETTLE, {b: _YTM})
        assert result.dv01 < 0

    def test_modified_duration_reasonable(self):
        b = _bond()
        result = _engine(b).bond_risk(_SETTLE, {b: _YTM})
        assert 5.0 < result.modified_duration < 12.0

    def test_convexity_positive(self):
        b = _bond()
        result = _engine(b).bond_risk(_SETTLE, {b: _YTM})
        assert result.convexity > 0

    def test_spread_dv01_positive(self):
        b = _bond()
        result = _engine(b, qty=1.0).bond_risk(
            _SETTLE, {b: _YTM}, spreads={b: 0.01}
        )
        assert result.spread_dv01 > 0
        assert result.spread_dv01 == pytest.approx(result.dv01, rel=1e-6)

    def test_mixed_portfolio_skips_non_bonds(self):
        b = _bond()
        cash = Cash(ticker="USD_CASH", currency=Currency.USD, multiplier=1)
        p = Portfolio(name="mixed")
        p.add_position(Position(instrument=b, quantity=1.0))
        p.add_position(Position(instrument=cash, quantity=1.0))
        engine = RiskEngine(p)
        result = engine.bond_risk(_SETTLE, {b: _YTM})
        assert isinstance(result.dv01, float)
        assert result.dv01 > 0

    def test_missing_ytm_raises_clear_error(self):
        b = _bond()
        with pytest.raises(ValueError, match="Missing YTM entries"):
            _engine(b).bond_risk(_SETTLE, {})
