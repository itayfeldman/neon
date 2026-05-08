import pytest

from neon.lib.greeks.analytical_greeks import AnalyticalGreeks
from neon.lib.instruments.options.european import EuropeanOption
from neon.lib.instruments.options.option_inputs import OptionInputs
from neon.lib.instruments.options.option_type import OptionType


def _inputs(
    underlying_price: float,
    strike_price: float,
    option_type: OptionType,
    volatility: float = 0.2,
    risk_free_rate: float = 0.05,
) -> OptionInputs:
    return OptionInputs(
        underlying_ticker="TEST",
        underlying_price=underlying_price,
        strike_price=strike_price,
        volatility=volatility,
        risk_free_rate=risk_free_rate,
        current_date="20250101",
        expiry_date="20260101",
        option_type=option_type,
    )


class TestPrice:
    def test_returns_float(self):
        opt = EuropeanOption(_inputs(100, 100, OptionType.Call), AnalyticalGreeks())
        assert isinstance(opt.price(), float)

    def test_atm_call_positive(self):
        opt = EuropeanOption(_inputs(100, 100, OptionType.Call), AnalyticalGreeks())
        assert opt.price() > 0

    def test_atm_put_positive(self):
        opt = EuropeanOption(_inputs(100, 100, OptionType.Put), AnalyticalGreeks())
        assert opt.price() > 0

    def test_atm_call_known_value(self):
        opt = EuropeanOption(_inputs(100, 100, OptionType.Call), AnalyticalGreeks())
        assert opt.price() == pytest.approx(10.4506, abs=0.01)

    def test_atm_put_known_value(self):
        opt = EuropeanOption(_inputs(100, 100, OptionType.Put), AnalyticalGreeks())
        assert opt.price() == pytest.approx(5.5735, abs=0.01)

    def test_call_increases_with_spot(self):
        prices = [
            EuropeanOption(_inputs(S, 100, OptionType.Call), AnalyticalGreeks()).price()
            for S in [80, 90, 100, 110, 120]
        ]
        assert prices == sorted(prices)

    def test_put_decreases_with_spot(self):
        prices = [
            EuropeanOption(_inputs(S, 100, OptionType.Put), AnalyticalGreeks()).price()
            for S in [80, 90, 100, 110, 120]
        ]
        assert prices == sorted(prices, reverse=True)


class TestGreeks:
    def test_delta_call_between_zero_and_one(self):
        opt = EuropeanOption(_inputs(100, 100, OptionType.Call), AnalyticalGreeks())
        assert 0.0 < opt.delta() < 1.0

    def test_delta_put_between_neg_one_and_zero(self):
        opt = EuropeanOption(_inputs(100, 100, OptionType.Put), AnalyticalGreeks())
        assert -1.0 < opt.delta() < 0.0

    def test_gamma_positive(self):
        opt = EuropeanOption(_inputs(100, 100, OptionType.Call), AnalyticalGreeks())
        assert opt.gamma() > 0

    def test_vega_positive(self):
        opt = EuropeanOption(_inputs(100, 100, OptionType.Call), AnalyticalGreeks())
        assert opt.vega() > 0

    def test_theta_negative(self):
        opt = EuropeanOption(_inputs(100, 100, OptionType.Call), AnalyticalGreeks())
        assert opt.theta() < 0

    def test_rho_positive_for_call(self):
        opt = EuropeanOption(_inputs(100, 100, OptionType.Call), AnalyticalGreeks())
        assert opt.rho() > 0
