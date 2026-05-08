import pytest

from neon.lib.instruments.cash import Cash
from neon.lib.portfolio.portfolio import Portfolio
from neon.lib.portfolio.position import Position


def _cash() -> Cash:
    return Cash()


def _pos(quantity: float) -> Position:
    return Position(instrument=_cash(), quantity=quantity)


class TestPortfolioValue:
    def test_empty_portfolio_value_is_zero(self):
        p = Portfolio(name="test")
        assert p.value() == pytest.approx(0.0)

    def test_returns_float(self):
        p = Portfolio(name="test")
        assert isinstance(p.value(), float)

    def test_single_long_position(self):
        p = Portfolio(name="test")
        p.add_position(_pos(10.0))
        assert p.value() == pytest.approx(10.0)

    def test_single_short_position(self):
        p = Portfolio(name="test")
        p.add_position(_pos(-5.0))
        assert p.value() == pytest.approx(-5.0)

    def test_mixed_positions_sum(self):
        p = Portfolio(name="test")
        p.add_position(_pos(10.0))
        p.add_position(_pos(-3.0))
        assert p.value() == pytest.approx(7.0)

    def test_multiple_long_positions_sum(self):
        p = Portfolio(name="test")
        p.add_position(_pos(4.0))
        p.add_position(_pos(6.0))
        assert p.value() == pytest.approx(10.0)


class TestPortfolioAddPosition:
    def test_add_position_appends(self):
        p = Portfolio(name="test")
        pos = _pos(1.0)
        p.add_position(pos)
        assert pos in p.positions

    def test_add_multiple_positions(self):
        p = Portfolio(name="test")
        p.add_position(_pos(1.0))
        p.add_position(_pos(2.0))
        assert len(p.positions) == 2
