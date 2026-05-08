import numpy as np

from neon.lib.greeks.analytical_greeks import AnalyticalGreeks
from neon.lib.instruments.options.asian import AsianOption
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
        opt = AsianOption(_inputs(100, 100, OptionType.Call), n_sim=1000)
        assert isinstance(opt.price(), float)

    def test_atm_call_positive(self):
        np.random.seed(42)
        opt = AsianOption(_inputs(100, 100, OptionType.Call), n_sim=5000)
        assert opt.price() > 0

    def test_atm_put_positive(self):
        np.random.seed(42)
        opt = AsianOption(_inputs(100, 100, OptionType.Put), n_sim=5000)
        assert opt.price() > 0

    def test_price_nonnegative(self):
        for S, K, t in [(100, 100, OptionType.Call), (100, 100, OptionType.Put),
                        (50, 100, OptionType.Call), (150, 100, OptionType.Put)]:
            np.random.seed(0)
            assert AsianOption(_inputs(S, K, t), n_sim=2000).price() >= 0

    def test_asian_call_le_european_call(self):
        np.random.seed(42)
        asian = AsianOption(_inputs(100, 100, OptionType.Call), n_sim=20000).price()
        european = EuropeanOption(
            _inputs(100, 100, OptionType.Call), AnalyticalGreeks()
        ).price()
        assert asian <= european + 0.5

    def test_call_increases_with_spot(self):
        prices = []
        for S in [80, 90, 100, 110, 120]:
            np.random.seed(42)
            opt = AsianOption(_inputs(S, 100, OptionType.Call), n_sim=10000)
            prices.append(opt.price())
        assert prices == sorted(prices)

    def test_put_decreases_with_spot(self):
        prices = []
        for S in [80, 90, 100, 110, 120]:
            np.random.seed(42)
            opt = AsianOption(_inputs(S, 100, OptionType.Put), n_sim=10000)
            prices.append(opt.price())
        assert prices == sorted(prices, reverse=True)
