import numpy as np  # noqa: I001
import pytest
from scipy.stats import norm

from neon.lib.greeks.analytical_greeks import AnalyticalGreeks
from neon.lib.greeks.numerical_greeks import NumericalGreeks
from neon.lib.instruments.options.option_type import OptionType


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _bs_price(
    underlying_price: float,
    strike_price: float,
    volatility: float,
    risk_free_rate: float,
    time_to_maturity: float,
    option_type: int,
) -> float:
    """Black-Scholes pricing via AnalyticalGreeks — used as the pricing_fn."""
    g = AnalyticalGreeks()
    g.underlying_price = underlying_price
    g.strike_price = strike_price
    g.volatility = volatility
    g.risk_free_rate = risk_free_rate
    g.time_to_maturity = time_to_maturity
    g.option_type = option_type
    return g.price()


def _make_numerical(
    underlying_price: float,
    strike_price: float,
    volatility: float,
    risk_free_rate: float,
    time_to_maturity: float,
    option_type: OptionType,
) -> NumericalGreeks:
    ng = NumericalGreeks(pricing_fn=_bs_price)
    ng.underlying_price = underlying_price
    ng.strike_price = strike_price
    ng.volatility = volatility
    ng.risk_free_rate = risk_free_rate
    ng.time_to_maturity = time_to_maturity
    ng.option_type = option_type
    return ng


def _make_pair(
    underlying_price: float,
    strike_price: float,
    volatility: float,
    risk_free_rate: float,
    time_to_maturity: float,
    option_type: OptionType,
) -> tuple[AnalyticalGreeks, NumericalGreeks]:
    """Return (analytical, numerical) Greeks with identical market data."""
    ag = AnalyticalGreeks()
    ag.underlying_price = underlying_price
    ag.strike_price = strike_price
    ag.volatility = volatility
    ag.risk_free_rate = risk_free_rate
    ag.time_to_maturity = time_to_maturity
    ag.option_type = option_type

    ng = _make_numerical(
        underlying_price,
        strike_price,
        volatility,
        risk_free_rate,
        time_to_maturity,
        option_type,
    )
    return ag, ng


def _bs_theta(S, K, sigma, r, T, phi):
    """Correct Black-Scholes theta for calls (phi=+1) and puts (phi=-1)."""
    d1 = (np.log(S / K) + (r + sigma**2 / 2) * T) / (sigma * np.sqrt(T))
    d2 = d1 - sigma * np.sqrt(T)
    return float(
        -(S * norm.pdf(d1) * sigma) / (2 * np.sqrt(T))
        - phi * r * K * np.exp(-r * T) * norm.cdf(phi * d2)
    )


def _bs_rho(S, K, sigma, r, T, phi):
    """Correct Black-Scholes rho for calls (phi=+1) and puts (phi=-1)."""
    d1 = (np.log(S / K) + (r + sigma**2 / 2) * T) / (sigma * np.sqrt(T))
    d2 = d1 - sigma * np.sqrt(T)
    return float(phi * K * T * np.exp(-r * T) * norm.cdf(phi * d2))


# Standard test parameters
ATM_CALL = (100, 100, 0.2, 0.05, 1.0, OptionType.Call)
ATM_PUT = (100, 100, 0.2, 0.05, 1.0, OptionType.Put)
ITM_CALL = (110, 100, 0.2, 0.05, 1.0, OptionType.Call)
OTM_CALL = (90, 100, 0.2, 0.05, 1.0, OptionType.Call)
ITM_PUT = (90, 100, 0.2, 0.05, 1.0, OptionType.Put)
OTM_PUT = (110, 100, 0.2, 0.05, 1.0, OptionType.Put)

ALL_CONFIGS = [ATM_CALL, ATM_PUT, ITM_CALL, OTM_CALL, ITM_PUT, OTM_PUT]
CALL_CONFIGS = [ATM_CALL, ITM_CALL, OTM_CALL]
PUT_CONFIGS = [ATM_PUT, ITM_PUT, OTM_PUT]


# ---------------------------------------------------------------------------
# price()
# ---------------------------------------------------------------------------


class TestPrice:
    def test_delegates_to_pricing_fn(self):
        ag, ng = _make_pair(*ATM_CALL)
        assert ng.price() == pytest.approx(ag.price(), abs=1e-10)

    @pytest.mark.parametrize("params", ALL_CONFIGS)
    def test_matches_analytical(self, params):
        ag, ng = _make_pair(*params)
        assert ng.price() == pytest.approx(ag.price(), abs=1e-10)


# ---------------------------------------------------------------------------
# delta()
# ---------------------------------------------------------------------------


class TestDelta:
    @pytest.mark.parametrize("params", ALL_CONFIGS)
    def test_matches_analytical(self, params):
        ag, ng = _make_pair(*params)
        assert ng.delta() == pytest.approx(ag.delta(), abs=0.01)

    def test_call_delta_between_zero_and_one(self):
        ng = _make_numerical(*ATM_CALL)
        assert 0.0 < ng.delta() < 1.0

    def test_put_delta_between_neg_one_and_zero(self):
        ng = _make_numerical(*ATM_PUT)
        assert -1.0 < ng.delta() < 0.0

    def test_itm_call_delta_above_atm(self):
        ng_atm = _make_numerical(*ATM_CALL)
        ng_itm = _make_numerical(*ITM_CALL)
        assert ng_itm.delta() > ng_atm.delta()

    def test_call_delta_increases_with_spot(self):
        deltas = [
            _make_numerical(s, 100, 0.2, 0.05, 1.0, OptionType.Call).delta()
            for s in [80, 90, 100, 110, 120]
        ]
        assert deltas == sorted(deltas)


# ---------------------------------------------------------------------------
# gamma()
# ---------------------------------------------------------------------------


class TestGamma:
    @pytest.mark.parametrize("params", ALL_CONFIGS)
    def test_matches_analytical(self, params):
        ag, ng = _make_pair(*params)
        assert ng.gamma() == pytest.approx(ag.gamma(), abs=0.01)

    def test_always_positive(self):
        for params in ALL_CONFIGS:
            ng = _make_numerical(*params)
            assert ng.gamma() > 0

    def test_higher_near_atm_than_deep_extremes(self):
        # Gamma peaks near S = K·exp(-(r+σ²/2)T) ≈ 93.2, not exactly ATM.
        # Use deep ITM/OTM to assert the general shape.
        ng_atm = _make_numerical(*ATM_CALL)
        ng_deep_itm = _make_numerical(150, 100, 0.2, 0.05, 1.0, OptionType.Call)
        ng_deep_otm = _make_numerical(60, 100, 0.2, 0.05, 1.0, OptionType.Call)
        assert ng_atm.gamma() > ng_deep_itm.gamma()
        assert ng_atm.gamma() > ng_deep_otm.gamma()


# ---------------------------------------------------------------------------
# vega()
# ---------------------------------------------------------------------------


class TestVega:
    @pytest.mark.parametrize("params", ALL_CONFIGS)
    def test_matches_analytical(self, params):
        ag, ng = _make_pair(*params)
        assert ng.vega() == pytest.approx(ag.vega(), abs=0.05)

    def test_always_positive(self):
        for params in ALL_CONFIGS:
            ng = _make_numerical(*params)
            assert ng.vega() > 0

    def test_peaks_near_atm(self):
        ng_atm = _make_numerical(*ATM_CALL)
        ng_deep_itm = _make_numerical(150, 100, 0.2, 0.05, 1.0, OptionType.Call)
        ng_deep_otm = _make_numerical(60, 100, 0.2, 0.05, 1.0, OptionType.Call)
        assert ng_atm.vega() > ng_deep_itm.vega()
        assert ng_atm.vega() > ng_deep_otm.vega()


# ---------------------------------------------------------------------------
# theta()
# ---------------------------------------------------------------------------


class TestTheta:
    @pytest.mark.parametrize("params", ALL_CONFIGS)
    def test_matches_correct_bs_theta(self, params):
        S, K, sigma, r, T, opt = params
        ng = _make_numerical(*params)
        expected = _bs_theta(S, K, sigma, r, T, int(opt))
        assert ng.theta() == pytest.approx(expected, abs=0.05)

    def test_negative_for_long_call(self):
        ng = _make_numerical(*ATM_CALL)
        assert ng.theta() < 0

    def test_negative_for_long_put(self):
        ng = _make_numerical(*ATM_PUT)
        assert ng.theta() < 0


# ---------------------------------------------------------------------------
# rho()
# ---------------------------------------------------------------------------


class TestRho:
    @pytest.mark.parametrize("params", ALL_CONFIGS)
    def test_matches_correct_bs_rho(self, params):
        S, K, sigma, r, T, opt = params
        ng = _make_numerical(*params)
        expected = _bs_rho(S, K, sigma, r, T, int(opt))
        assert ng.rho() == pytest.approx(expected, abs=0.01)

    def test_positive_for_call(self):
        ng = _make_numerical(*ATM_CALL)
        assert ng.rho() > 0

    def test_negative_for_put(self):
        ng = _make_numerical(*ATM_PUT)
        assert ng.rho() < 0


# ---------------------------------------------------------------------------
# vanna()
# ---------------------------------------------------------------------------


class TestVanna:
    @pytest.mark.parametrize("params", [ATM_CALL, ATM_PUT, ITM_CALL, OTM_CALL])
    def test_returns_finite_value(self, params):
        ng = _make_numerical(*params)
        v = ng.vanna()
        assert isinstance(v, float)
        assert abs(v) < 100  # sanity bound

    def test_call_put_same_magnitude(self):
        ng_call = _make_numerical(*ATM_CALL)
        ng_put = _make_numerical(*ATM_PUT)
        assert ng_call.vanna() == pytest.approx(ng_put.vanna(), abs=0.01)


# ---------------------------------------------------------------------------
# volga()
# ---------------------------------------------------------------------------


class TestVolga:
    @pytest.mark.parametrize("params", [ATM_CALL, ATM_PUT, ITM_CALL, OTM_CALL])
    def test_returns_finite_value(self, params):
        ng = _make_numerical(*params)
        v = ng.volga()
        assert isinstance(v, float)
        assert abs(v) < 1000  # sanity bound

    def test_call_put_same_magnitude(self):
        ng_call = _make_numerical(*ATM_CALL)
        ng_put = _make_numerical(*ATM_PUT)
        assert ng_call.volga() == pytest.approx(ng_put.volga(), abs=0.01)


# ---------------------------------------------------------------------------
# Liskov substitution — works inside EuropeanOption
# ---------------------------------------------------------------------------


class TestLSP:
    @pytest.mark.xfail(
        reason="Pre-existing format bug in base.py:11 serialize_option_inputs",
        strict=True,
    )
    def test_european_option_works_with_numerical_greeks(self):
        from neon.lib.instruments.options.european import EuropeanOption
        from neon.lib.instruments.options.option_inputs import OptionInputs

        inputs = OptionInputs(
            underlying_ticker="TEST",
            underlying_price=100,
            strike_price=100,
            volatility=0.2,
            risk_free_rate=0.05,
            current_date="20250101",
            expiry_date="20260101",
            option_type=OptionType.Call,
        )
        ng = NumericalGreeks(pricing_fn=_bs_price)
        ng.underlying_price = inputs.underlying_price
        ng.strike_price = inputs.strike_price
        ng.volatility = inputs.volatility
        ng.risk_free_rate = inputs.risk_free_rate
        ng.time_to_maturity = 1.0
        ng.option_type = inputs.option_type

        option = EuropeanOption(inputs, ng)
        assert isinstance(option.price(), float)
        assert option.price() > 0
        assert isinstance(option.delta(), float)
        assert isinstance(option.gamma(), float)
        assert isinstance(option.vega(), float)
        assert isinstance(option.theta(), float)
        assert isinstance(option.rho(), float)
