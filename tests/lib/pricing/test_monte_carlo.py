import numpy as np
import pytest

from neon.lib.pricing.monte_carlo import price_mc, simulate_gbm


class TestSimulateGbm:
    def test_output_shape(self):
        paths = simulate_gbm(S=100.0, r=0.05, sigma=0.2, T=1.0, steps=10, n_sim=50)
        assert paths.shape == (50, 11)

    def test_first_column_equals_spot(self):
        paths = simulate_gbm(S=100.0, r=0.05, sigma=0.2, T=1.0, steps=10, n_sim=100)
        assert np.allclose(paths[:, 0], 100.0)

    def test_all_prices_positive(self):
        paths = simulate_gbm(S=100.0, r=0.05, sigma=0.2, T=1.0, steps=50, n_sim=200)
        assert np.all(paths > 0)

    def test_higher_vol_wider_spread(self):
        np.random.seed(0)
        lo = simulate_gbm(S=100.0, r=0.05, sigma=0.1, T=1.0, steps=50, n_sim=1000)
        np.random.seed(0)
        hi = simulate_gbm(S=100.0, r=0.05, sigma=0.4, T=1.0, steps=50, n_sim=1000)
        assert hi[:, -1].std() > lo[:, -1].std()


class TestPriceMc:
    def test_returns_float(self):
        paths = simulate_gbm(S=100.0, r=0.05, sigma=0.2, T=1.0, steps=10, n_sim=50)
        payoff = lambda p: np.maximum(p[:, -1] - 100.0, 0.0)  # noqa: E731
        result = price_mc(paths, payoff, r=0.05, T=1.0)
        assert isinstance(result, float)

    def test_zero_payoff_gives_zero_price(self):
        paths = simulate_gbm(S=100.0, r=0.05, sigma=0.2, T=1.0, steps=10, n_sim=100)
        result = price_mc(paths, lambda p: np.zeros(len(p)), r=0.05, T=1.0)
        assert result == pytest.approx(0.0)

    def test_certain_payoff_gives_discounted_value(self):
        paths = simulate_gbm(S=100.0, r=0.05, sigma=0.2, T=1.0, steps=10, n_sim=100)
        result = price_mc(paths, lambda p: np.ones(len(p)), r=0.05, T=1.0)
        assert result == pytest.approx(np.exp(-0.05 * 1.0), rel=1e-6)

    def test_atm_call_positive(self):
        np.random.seed(42)
        paths = simulate_gbm(S=100.0, r=0.05, sigma=0.2, T=1.0, steps=252, n_sim=10000)
        payoff = lambda p: np.maximum(p[:, -1] - 100.0, 0.0)  # noqa: E731
        result = price_mc(paths, payoff, r=0.05, T=1.0)
        assert result > 0
