import math

import pytest

from neon.lib.instruments.options.local_vol_option import LocalVolOption
from neon.lib.instruments.options.option_type import OptionType
from neon.lib.instruments.surface.dupire import DupireLocalVol
from neon.lib.instruments.surface.svi import SVICalibrator, SVISurface

_F = 100.0
_T1, _T2 = 1.0, 2.0
_EXP1, _EXP2 = "20260101", "20270101"
_STRIKES = [80.0, 85.0, 90.0, 95.0, 100.0, 105.0, 110.0, 115.0, 120.0]
_SETTLE = "20250101"


def _surface() -> SVISurface:
    slice1 = SVICalibrator.fit(
        _STRIKES, _F, _T1,
        [0.25, 0.23, 0.21, 0.20, 0.20, 0.21, 0.22, 0.23, 0.25],
    )
    slice2 = SVICalibrator.fit(
        _STRIKES, _F, _T2,
        [0.24, 0.22, 0.21, 0.20, 0.20, 0.20, 0.21, 0.22, 0.24],
    )
    return SVISurface(
        slices={_EXP1: slice1, _EXP2: slice2},
        forwards={_EXP1: _F, _EXP2: _F},
        times={_EXP1: _T1, _EXP2: _T2},
    )


def _local_vol() -> DupireLocalVol:
    return DupireLocalVol(_surface())


def _call() -> LocalVolOption:
    return LocalVolOption(
        underlying_price=_F,
        strike=100.0,
        risk_free_rate=0.03,
        current_date=_SETTLE,
        expiry_date=_EXP1,
        option_type=OptionType.Call,
        local_vol=_local_vol(),
    )


def _put() -> LocalVolOption:
    return LocalVolOption(
        underlying_price=_F,
        strike=100.0,
        risk_free_rate=0.03,
        current_date=_SETTLE,
        expiry_date=_EXP1,
        option_type=OptionType.Put,
        local_vol=_local_vol(),
    )


class TestLocalVolOption:
    def test_price_returns_float(self):
        assert isinstance(_call().price(), float)

    def test_call_price_positive(self):
        assert _call().price() > 0

    def test_put_price_positive(self):
        assert _put().price() > 0

    def test_put_call_parity(self):
        # C - P = S - K*e^(-rT); with S=K=100, r=0.03, T=1 this is ~2.96
        call = _call().price()
        put = _put().price()
        expected = _F - _F * math.exp(-0.03 * _T1)
        assert abs((call - put) - expected) < 1.0

    def test_itm_call_more_expensive_than_otm(self):
        lv = _local_vol()
        itm = LocalVolOption(
            underlying_price=_F, strike=90.0, risk_free_rate=0.03,
            current_date=_SETTLE, expiry_date=_EXP1,
            option_type=OptionType.Call, local_vol=lv,
        ).price()
        otm = LocalVolOption(
            underlying_price=_F, strike=110.0, risk_free_rate=0.03,
            current_date=_SETTLE, expiry_date=_EXP1,
            option_type=OptionType.Call, local_vol=lv,
        ).price()
        assert itm > otm

    def test_longer_expiry_higher_call_price(self):
        lv = _local_vol()
        short = LocalVolOption(
            underlying_price=_F, strike=100.0, risk_free_rate=0.03,
            current_date=_SETTLE, expiry_date=_EXP1,
            option_type=OptionType.Call, local_vol=lv,
        ).price()
        long_ = LocalVolOption(
            underlying_price=_F, strike=100.0, risk_free_rate=0.03,
            current_date=_SETTLE, expiry_date=_EXP2,
            option_type=OptionType.Call, local_vol=lv,
        ).price()
        assert long_ > short

    def test_price_reasonable_magnitude(self):
        # ATM call with ~20% vol and T=1 should be roughly 7–10% of spot
        p = _call().price()
        assert 1.0 < p < 25.0

    def test_raises_for_non_positive_time_to_expiry(self):
        with pytest.raises(ValueError, match="expiry_date must be after current_date"):
            LocalVolOption(
                underlying_price=_F,
                strike=100.0,
                risk_free_rate=0.03,
                current_date=_SETTLE,
                expiry_date=_SETTLE,
                option_type=OptionType.Call,
                local_vol=_local_vol(),
            )

    @pytest.mark.parametrize(
        ("n_spots", "n_steps"), [(0, 100), (100, 0), (-1, 10), (10, -1)]
    )
    def test_raises_for_non_positive_grid_sizes(self, n_spots: int, n_steps: int):
        with pytest.raises(ValueError, match="must be positive"):
            LocalVolOption(
                underlying_price=_F,
                strike=100.0,
                risk_free_rate=0.03,
                current_date=_SETTLE,
                expiry_date=_EXP1,
                option_type=OptionType.Call,
                local_vol=_local_vol(),
                n_spots=n_spots,
                n_steps=n_steps,
            )
