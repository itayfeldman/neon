import pytest

from neon.lib.instruments.cash import Cash
from neon.lib.portfolio.portfolio import Portfolio
from neon.lib.portfolio.position import Position
from neon.lib.risk.risk_engine import RiskEngine


def _pos(quantity: float) -> Position:
    return Position(instrument=Cash(), quantity=quantity)


def _engine(*quantities: float) -> RiskEngine:
    p = Portfolio(name="test")
    for q in quantities:
        p.add_position(_pos(q))
    return RiskEngine(p)


# Cash uses Greeks() base class:
#   delta=1.0, gamma=0.0, vega=0.0, theta=0.0, rho=0.0, vanna=0.0, volga=0.0


class TestReturnTypes:
    def test_net_delta_returns_float(self):
        assert isinstance(_engine(1.0).net_delta(), float)

    def test_net_gamma_returns_float(self):
        assert isinstance(_engine(1.0).net_gamma(), float)

    def test_net_vega_returns_float(self):
        assert isinstance(_engine(1.0).net_vega(), float)

    def test_net_theta_returns_float(self):
        assert isinstance(_engine(1.0).net_theta(), float)

    def test_net_rho_returns_float(self):
        assert isinstance(_engine(1.0).net_rho(), float)

    def test_net_vanna_returns_float(self):
        assert isinstance(_engine(1.0).net_vanna(), float)

    def test_net_volga_returns_float(self):
        assert isinstance(_engine(1.0).net_volga(), float)


class TestEmptyPortfolio:
    def test_net_delta_zero(self):
        assert _engine().net_delta() == pytest.approx(0.0)

    def test_net_gamma_zero(self):
        assert _engine().net_gamma() == pytest.approx(0.0)

    def test_net_vega_zero(self):
        assert _engine().net_vega() == pytest.approx(0.0)

    def test_net_theta_zero(self):
        assert _engine().net_theta() == pytest.approx(0.0)

    def test_net_rho_zero(self):
        assert _engine().net_rho() == pytest.approx(0.0)

    def test_net_vanna_zero(self):
        assert _engine().net_vanna() == pytest.approx(0.0)

    def test_net_volga_zero(self):
        assert _engine().net_volga() == pytest.approx(0.0)


class TestSinglePosition:
    def test_long_delta(self):
        # Cash.greeks.delta() == 1.0; quantity=5 → net_delta=5.0
        assert _engine(5.0).net_delta() == pytest.approx(5.0)

    def test_short_delta(self):
        assert _engine(-3.0).net_delta() == pytest.approx(-3.0)

    def test_zero_quantity_delta(self):
        assert _engine(0.0).net_delta() == pytest.approx(0.0)

    def test_gamma_zero_for_cash(self):
        # Greeks().gamma() == 0.0
        assert _engine(10.0).net_gamma() == pytest.approx(0.0)


class TestMultiplePositions:
    def test_two_longs_sum(self):
        assert _engine(3.0, 4.0).net_delta() == pytest.approx(7.0)

    def test_long_and_short_cancel(self):
        assert _engine(5.0, -5.0).net_delta() == pytest.approx(0.0)

    def test_mixed_net_delta(self):
        assert _engine(10.0, -3.0).net_delta() == pytest.approx(7.0)
