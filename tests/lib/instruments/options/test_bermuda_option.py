import pytest

from neon.lib.greeks.analytical_greeks import AnalyticalGreeks
from neon.lib.instruments.options.american import AmericanOption
from neon.lib.instruments.options.bermuda import BermudaOption
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


# Monthly exercise dates between 20250101 and 20260101
MONTHLY = [
    "20250201", "20250301", "20250401", "20250501",
    "20250601", "20250701", "20250801", "20250901",
    "20251001", "20251101", "20251201",
]


class TestPrice:
    def test_returns_float(self):
        opt = BermudaOption(_inputs(100, 100, OptionType.Call), exercise_dates=MONTHLY)
        assert isinstance(opt.price(), float)

    def test_atm_call_positive(self):
        opt = BermudaOption(_inputs(100, 100, OptionType.Call), exercise_dates=MONTHLY)
        assert opt.price() > 0

    def test_atm_put_positive(self):
        opt = BermudaOption(_inputs(100, 100, OptionType.Put), exercise_dates=MONTHLY)
        assert opt.price() > 0

    def test_price_nonnegative(self):
        for S, K, t in [(100, 100, OptionType.Call), (100, 100, OptionType.Put),
                        (50, 100, OptionType.Put), (150, 100, OptionType.Call)]:
            assert BermudaOption(_inputs(S, K, t), exercise_dates=MONTHLY).price() >= 0


class TestSandwich:
    """European ≤ Bermuda ≤ American"""

    def test_put_sandwich(self):
        inp = _inputs(100, 100, OptionType.Put)
        european = EuropeanOption(inp, AnalyticalGreeks()).price()
        bermuda = BermudaOption(inp, exercise_dates=MONTHLY).price()
        american = AmericanOption(inp).price()
        assert european <= bermuda + 0.01
        assert bermuda <= american + 0.01

    def test_call_sandwich(self):
        inp = _inputs(100, 100, OptionType.Call)
        european = EuropeanOption(inp, AnalyticalGreeks()).price()
        bermuda = BermudaOption(inp, exercise_dates=MONTHLY).price()
        american = AmericanOption(inp).price()
        assert european <= bermuda + 0.01
        assert bermuda <= american + 0.01

    def test_expiry_only_approx_european(self):
        inp = _inputs(100, 100, OptionType.Put)
        bermuda = BermudaOption(inp, exercise_dates=["20260101"]).price()
        european = EuropeanOption(inp, AnalyticalGreeks()).price()
        assert bermuda == pytest.approx(european, rel=0.02)
