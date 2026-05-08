import numpy as np
import pytest
from scipy.stats import norm

from neon.lib.greeks.analytical_greeks import AnalyticalGreeks
from neon.lib.instruments.options.option_type import OptionType


def make_european_option_analytical_greeks(
    underlying_price: float,
    strike_price: float,
    volatility: float,
    risk_free_rate: float,
    time_to_maturity: float,
    option_type: OptionType,
) -> AnalyticalGreeks:
    g = AnalyticalGreeks()
    g.underlying_price = underlying_price
    g.strike_price = strike_price
    g.volatility = volatility
    g.risk_free_rate = risk_free_rate
    g.time_to_maturity = time_to_maturity
    g.option_type = option_type
    return g


def make_greeks(
    underlying_price: float,
    strike_price: float,
    volatility: float,
    risk_free_rate: float,
    time_to_maturity: float,
    option_type: OptionType,
) -> AnalyticalGreeks:
    g = AnalyticalGreeks()
    g.underlying_price = underlying_price
    g.strike_price = strike_price
    g.volatility = volatility
    g.risk_free_rate = risk_free_rate
    g.time_to_maturity = time_to_maturity
    g.option_type = option_type
    return g


# ---------------------------------------------------------------------------
# Helper properties
# ---------------------------------------------------------------------------


class TestHelpers:
    def test_a_equals_vol_times_sqrt_ttm(self):
        g = make_greeks(100, 100, 0.2, 0.05, 1.0, OptionType.Call)
        assert g._a_ == pytest.approx(0.2 * np.sqrt(1.0))

    def test_a_uses_ttm_correctly(self):
        g = make_greeks(100, 100, 0.3, 0.05, 0.5, OptionType.Call)
        assert g._a_ == pytest.approx(0.3 * np.sqrt(0.5))

    def test_b_equals_discount_factor(self):
        g = make_greeks(100, 100, 0.2, 0.05, 1.0, OptionType.Call)
        assert g._b_ == pytest.approx(np.exp(-0.05))

    def test_b_is_one_when_rate_is_zero(self):
        g = make_greeks(100, 100, 0.2, 0.0, 1.0, OptionType.Call)
        assert g._b_ == pytest.approx(1.0)


# ---------------------------------------------------------------------------
# d1 / d2
# ---------------------------------------------------------------------------


class TestD1D2:
    def test_d1_atm(self):
        # S=K=100, σ=0.2, r=0.05, T=1 → d1 = 0.07/0.2 = 0.35
        g = make_greeks(100, 100, 0.2, 0.05, 1.0, OptionType.Call)
        expected = (np.log(1.0) + (0.05 + 0.02) * 1.0) / (0.2 * np.sqrt(1.0))
        assert g.d1 == pytest.approx(expected)

    def test_d2_equals_d1_minus_a(self):
        g = make_greeks(100, 100, 0.2, 0.05, 1.0, OptionType.Call)
        assert g.d2 == pytest.approx(g.d1 - g._a_)

    def test_d1_higher_when_itm(self):
        atm = make_greeks(100, 100, 0.2, 0.05, 1.0, OptionType.Call)
        itm = make_greeks(110, 100, 0.2, 0.05, 1.0, OptionType.Call)
        assert itm.d1 > atm.d1

    def test_d1_lower_when_otm(self):
        atm = make_greeks(100, 100, 0.2, 0.05, 1.0, OptionType.Call)
        otm = make_greeks(90, 100, 0.2, 0.05, 1.0, OptionType.Call)
        assert otm.d1 < atm.d1


# ---------------------------------------------------------------------------
# price()
# ---------------------------------------------------------------------------


class TestPrice:
    def test_returns_float(self):
        g = make_greeks(100, 100, 0.2, 0.05, 1.0, OptionType.Call)
        assert isinstance(g.price(), float)

    def test_call_price_positive(self):
        g = make_greeks(100, 100, 0.2, 0.05, 1.0, OptionType.Call)
        assert g.price() > 0

    def test_put_price_positive(self):
        g = make_greeks(100, 100, 0.2, 0.05, 1.0, OptionType.Put)
        assert g.price() > 0

    def test_atm_call_known_value(self):
        # S=K=100, σ=0.2, r=0.05, T=1 → ~10.45
        g = make_greeks(100, 100, 0.2, 0.05, 1.0, OptionType.Call)
        assert g.price() == pytest.approx(10.4506, abs=0.01)

    def test_atm_put_known_value(self):
        # S=K=100, σ=0.2, r=0.05, T=1 → ~5.57
        g = make_greeks(100, 100, 0.2, 0.05, 1.0, OptionType.Put)
        assert g.price() == pytest.approx(5.5735, abs=0.01)

    def test_put_call_parity(self):
        S, K, sigma, r, T = 100, 100, 0.2, 0.05, 1.0
        call = make_greeks(S, K, sigma, r, T, OptionType.Call).price()
        put = make_greeks(S, K, sigma, r, T, OptionType.Put).price()
        assert call - put == pytest.approx(S - K * np.exp(-r * T), abs=1e-6)

    def test_put_call_parity_off_strike(self):
        S, K, sigma, r, T = 105, 100, 0.25, 0.03, 0.5
        call = make_greeks(S, K, sigma, r, T, OptionType.Call).price()
        put = make_greeks(S, K, sigma, r, T, OptionType.Put).price()
        assert call - put == pytest.approx(S - K * np.exp(-r * T), abs=1e-6)

    def test_call_matches_bs_formula(self):
        S, K, sigma, r, T = 110, 100, 0.2, 0.05, 1.0
        d1 = (np.log(S / K) + (r + sigma**2 / 2) * T) / (sigma * np.sqrt(T))
        d2 = d1 - sigma * np.sqrt(T)
        expected = S * norm.cdf(d1) - K * np.exp(-r * T) * norm.cdf(d2)
        g = make_greeks(S, K, sigma, r, T, OptionType.Call)
        assert g.price() == pytest.approx(expected, rel=1e-6)

    def test_put_matches_bs_formula(self):
        S, K, sigma, r, T = 90, 100, 0.2, 0.05, 1.0
        d1 = (np.log(S / K) + (r + sigma**2 / 2) * T) / (sigma * np.sqrt(T))
        d2 = d1 - sigma * np.sqrt(T)
        expected = K * np.exp(-r * T) * norm.cdf(-d2) - S * norm.cdf(-d1)
        g = make_greeks(S, K, sigma, r, T, OptionType.Put)
        assert g.price() == pytest.approx(expected, rel=1e-6)

    def test_deep_itm_call_approaches_forward(self):
        # S >> K: call price ≈ S - K·e^(−rT)
        S, K, r, T = 200, 100, 0.05, 1.0
        g = make_greeks(S, K, 0.2, r, T, OptionType.Call)
        assert g.price() == pytest.approx(S - K * np.exp(-r * T), rel=0.01)

    def test_deep_otm_call_near_zero(self):
        g = make_greeks(50, 100, 0.2, 0.05, 1.0, OptionType.Call)
        assert g.price() < 0.01

    def test_deep_otm_put_near_zero(self):
        g = make_greeks(200, 100, 0.2, 0.05, 1.0, OptionType.Put)
        assert g.price() < 0.01

    def test_call_increases_with_underlying(self):
        prices = [
            make_greeks(S, 100, 0.2, 0.05, 1.0, OptionType.Call).price()
            for S in [90, 100, 110, 120]
        ]
        assert prices == sorted(prices)

    def test_put_decreases_with_underlying(self):
        prices = [
            make_greeks(S, 100, 0.2, 0.05, 1.0, OptionType.Put).price()
            for S in [90, 100, 110, 120]
        ]
        assert prices == sorted(prices, reverse=True)

    def test_call_increases_with_volatility(self):
        prices = [
            make_greeks(100, 100, vol, 0.05, 1.0, OptionType.Call).price()
            for vol in [0.1, 0.2, 0.3, 0.4]
        ]
        assert prices == sorted(prices)

    def test_put_increases_with_volatility(self):
        prices = [
            make_greeks(100, 100, vol, 0.05, 1.0, OptionType.Put).price()
            for vol in [0.1, 0.2, 0.3, 0.4]
        ]
        assert prices == sorted(prices)

    def test_call_increases_with_time_to_maturity(self):
        prices = [
            make_greeks(100, 100, 0.2, 0.05, T, OptionType.Call).price()
            for T in [0.25, 0.5, 1.0, 2.0]
        ]
        assert prices == sorted(prices)
