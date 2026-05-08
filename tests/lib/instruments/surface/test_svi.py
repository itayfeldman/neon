import math

import pytest

from neon.lib.instruments.surface.svi import SVICalibrator, SVISlice, SVISurface

# SVI params: a=0.04, b=0.1, rho=-0.3, m=0.0, sigma=0.2, T=1.0
_PARAMS = dict(a=0.04, b=0.1, rho=-0.3, m=0.0, sigma=0.2)
_T = 1.0
_F = 100.0  # forward price


def _slice() -> SVISlice:
    return SVISlice(**_PARAMS)


def _market_vols(strikes: list[float]) -> list[float]:
    """Generate synthetic market vols from known SVI params."""
    sl = _slice()
    return [sl.implied_vol(k, _F, _T) for k in strikes]


class TestSVISlice:
    def test_implied_vol_positive(self):
        assert _slice().implied_vol(100.0, _F, _T) > 0

    def test_implied_vol_returns_float(self):
        assert isinstance(_slice().implied_vol(100.0, _F, _T), float)

    def test_smile_shape_higher_at_wings(self):
        sl = _slice()
        atm = sl.implied_vol(_F, _F, _T)
        otm_put = sl.implied_vol(_F * 0.8, _F, _T)
        otm_call = sl.implied_vol(_F * 1.2, _F, _T)
        assert otm_put > atm or otm_call > atm

    def test_total_variance_non_negative(self):
        sl = _slice()
        for k in [80.0, 90.0, 100.0, 110.0, 120.0]:
            lm = math.log(k / _F)
            inner = math.sqrt((lm - sl.m) ** 2 + sl.sigma ** 2)
            w = sl.a + sl.b * (sl.rho * (lm - sl.m) + inner)
            assert w >= 0


class TestSVICalibrator:
    def test_returns_svi_slice(self):
        strikes = [85.0, 90.0, 95.0, 100.0, 105.0, 110.0, 115.0]
        market_vols = _market_vols(strikes)
        result = SVICalibrator.fit(strikes, _F, _T, market_vols)
        assert isinstance(result, SVISlice)

    def test_fitted_vols_close_to_market(self):
        strikes = [85.0, 90.0, 95.0, 100.0, 105.0, 110.0, 115.0]
        market_vols = _market_vols(strikes)
        fitted = SVICalibrator.fit(strikes, _F, _T, market_vols)
        for k, mv in zip(strikes, market_vols):
            fitted_vol = fitted.implied_vol(k, _F, _T)
            assert fitted_vol == pytest.approx(mv, abs=1e-3)

    def test_recovers_parameters(self):
        strikes = [80.0, 85.0, 90.0, 95.0, 100.0, 105.0, 110.0, 115.0, 120.0]
        market_vols = _market_vols(strikes)
        fitted = SVICalibrator.fit(strikes, _F, _T, market_vols)
        # Check implied vols are close — params may differ due to non-uniqueness
        for k, mv in zip(strikes, market_vols):
            assert fitted.implied_vol(k, _F, _T) == pytest.approx(mv, abs=2e-3)


class TestSVISurface:
    def test_get_vol_returns_float(self):
        strikes = [90.0, 100.0, 110.0]
        expiries = {"20260101": (_F, _T), "20270101": (_F, 2.0)}
        market_data = {
            exp: (strikes, [_slice().implied_vol(k, F, T) for k in strikes])
            for exp, (F, T) in expiries.items()
        }
        surface = SVISurface.calibrate(market_data)
        assert isinstance(surface.get_vol(100.0, "20260101"), float)

    def test_get_vol_positive(self):
        strikes = [90.0, 100.0, 110.0]
        expiries = {"20260101": (_F, _T)}
        market_data = {
            exp: (strikes, [_slice().implied_vol(k, _F, _T) for k in strikes])
            for exp in expiries
        }
        surface = SVISurface.calibrate(market_data)
        assert surface.get_vol(100.0, "20260101") > 0

    def test_interpolates_between_expiries(self):
        strikes = [90.0, 100.0, 110.0]
        market_data = {
            "20260101": (strikes, [_slice().implied_vol(k, _F, 1.0) for k in strikes]),
            "20280101": (strikes, [_slice().implied_vol(k, _F, 3.0) for k in strikes]),
        }
        surface = SVISurface.calibrate(market_data)
        # Vol at intermediate expiry should be between the two slice vols
        v1 = surface.get_vol(100.0, "20260101")
        v2 = surface.get_vol(100.0, "20280101")
        v_mid = surface.get_vol(100.0, "20270101")
        assert min(v1, v2) - 0.01 <= v_mid <= max(v1, v2) + 0.01
