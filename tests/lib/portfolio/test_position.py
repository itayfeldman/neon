import pytest

from neon.lib.instruments.cash import Cash
from neon.lib.portfolio.position import Position


def _cash() -> Cash:
    return Cash()


class TestPositionValue:
    def test_returns_float(self):
        pos = Position(instrument=_cash(), quantity=10.0)
        assert isinstance(pos.value(), float)

    def test_long_positive_value(self):
        pos = Position(instrument=_cash(), quantity=5.0)
        assert pos.value() == pytest.approx(5.0)

    def test_short_negative_value(self):
        pos = Position(instrument=_cash(), quantity=-3.0)
        assert pos.value() == pytest.approx(-3.0)

    def test_zero_quantity_zero_value(self):
        pos = Position(instrument=_cash(), quantity=0.0)
        assert pos.value() == pytest.approx(0.0)

    def test_value_scales_with_price(self):
        # Cash.price() == 1.0; value == quantity * 1.0
        pos = Position(instrument=_cash(), quantity=7.0)
        assert pos.value() == pytest.approx(7.0 * _cash().price())


class TestPositionImmutability:
    def test_is_frozen(self):
        pos = Position(instrument=_cash(), quantity=10.0)
        with pytest.raises((AttributeError, TypeError)):
            pos.quantity = 99.0
