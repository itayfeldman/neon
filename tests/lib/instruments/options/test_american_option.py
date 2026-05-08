import pytest

from neon.lib.greeks.analytical_greeks import AnalyticalGreeks
from neon.lib.instruments.options.american import AmericanOption
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


def _ag(inputs: OptionInputs) -> AnalyticalGreeks:
    ag = AnalyticalGreeks()
    ag.underlying_price = inputs.underlying_price
    ag.strike_price = inputs.strike_price
    ag.volatility = inputs.volatility
    ag.risk_free_rate = inputs.risk_free_rate
    ag.time_to_maturity = 1.0
    ag.option_type = inputs.option_type
    return ag


# ---------------------------------------------------------------------------
# price()
# ---------------------------------------------------------------------------


class TestPrice:
    def test_returns_float(self):
        opt = AmericanOption(_inputs(100, 100, OptionType.Call))
        assert isinstance(opt.price(), float)

    def test_atm_call_positive(self):
        opt = AmericanOption(_inputs(100, 100, OptionType.Call))
        assert opt.price() > 0

    def test_atm_put_positive(self):
        opt = AmericanOption(_inputs(100, 100, OptionType.Put))
        assert opt.price() > 0

    def test_price_always_nonnegative(self):
        for S, K, opt_type in [
            (100, 100, OptionType.Call),
            (100, 100, OptionType.Put),
            (110, 100, OptionType.Call),
            (90, 100, OptionType.Put),
            (50, 100, OptionType.Call),
            (150, 100, OptionType.Put),
        ]:
            assert AmericanOption(_inputs(S, K, opt_type)).price() >= 0


class TestEarlyExercisePremium:
    def test_american_call_ge_european_call(self):
        inp = _inputs(100, 100, OptionType.Call)
        american = AmericanOption(inp).price()
        ag = _ag(inp)
        european = ag.price()
        # CRR tree converges from below with finite steps; allow discretisation error
        assert american >= european - 0.02

    def test_american_put_gt_european_put(self):
        # Early exercise premium on puts is positive when rates > 0
        inp = _inputs(100, 100, OptionType.Put)
        american = AmericanOption(inp).price()
        ag = _ag(inp)
        european = ag.price()
        assert american > european

    def test_deep_itm_put_early_exercise_premium(self):
        # Deep ITM put: American price >> European
        inp = _inputs(60, 100, OptionType.Put)
        american = AmericanOption(inp).price()
        ag = _ag(inp)
        european = ag.price()
        assert american > european

    def test_call_increases_with_spot(self):
        prices = [
            AmericanOption(_inputs(S, 100, OptionType.Call)).price()
            for S in [80, 90, 100, 110, 120]
        ]
        assert prices == sorted(prices)

    def test_put_decreases_with_spot(self):
        prices = [
            AmericanOption(_inputs(S, 100, OptionType.Put)).price()
            for S in [80, 90, 100, 110, 120]
        ]
        assert prices == sorted(prices, reverse=True)


class TestAtmCallApproximation:
    def test_atm_call_close_to_black_scholes(self):
        inp = _inputs(100, 100, OptionType.Call)
        american = AmericanOption(inp).price()
        ag = _ag(inp)
        assert american == pytest.approx(ag.price(), rel=0.02)


# ---------------------------------------------------------------------------
# LSP — AmericanOption is substitutable for BaseOption
# ---------------------------------------------------------------------------


class TestLSP:
    def test_is_base_option_subtype(self):
        from neon.lib.instruments.options.base import BaseOption
        opt = AmericanOption(_inputs(100, 100, OptionType.Call))
        assert isinstance(opt, BaseOption)

    def test_has_price_method(self):
        opt = AmericanOption(_inputs(100, 100, OptionType.Call))
        result = opt.price()
        assert isinstance(result, float)
