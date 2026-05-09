import pytest

from neon.lib.instruments.surface.dupire import DupireLocalVol
from neon.lib.instruments.surface.svi import SVICalibrator, SVISurface

_F = 100.0
_T1, _T2 = 1.0, 2.0
_EXP1, _EXP2 = "20260101", "20270101"
_STRIKES = [80.0, 85.0, 90.0, 95.0, 100.0, 105.0, 110.0, 115.0, 120.0]


def _surface() -> SVISurface:
    slice1 = SVICalibrator.fit(
        _STRIKES, _F, _T1,
        [0.25, 0.23, 0.21, 0.20, 0.20, 0.21, 0.22, 0.23, 0.25],
    )
    slice2 = SVICalibrator.fit(
        _STRIKES, _F, _T2,
        [0.24, 0.22, 0.21, 0.20, 0.20, 0.20, 0.21, 0.22, 0.24],
    )
    surface = SVISurface(
        slices={_EXP1: slice1, _EXP2: slice2},
        forwards={_EXP1: _F, _EXP2: _F},
        times={_EXP1: _T1, _EXP2: _T2},
    )
    return surface


def _dupire() -> DupireLocalVol:
    return DupireLocalVol(_surface())


class TestDupireLocalVol:
    def test_local_vol_returns_float(self):
        assert isinstance(_dupire().local_vol(100.0, 1.0), float)

    def test_local_vol_positive(self):
        assert _dupire().local_vol(100.0, 1.0) > 0

    def test_local_vol_reasonable_magnitude(self):
        # Local vol should be in the same ballpark as implied vol (0.1 – 0.6)
        lv = _dupire().local_vol(100.0, 1.0)
        assert 0.05 < lv < 1.0

    def test_local_vol_varies_by_strike(self):
        d = _dupire()
        lv_atm = d.local_vol(100.0, 1.0)
        lv_otm = d.local_vol(80.0, 1.0)
        assert lv_atm != pytest.approx(lv_otm, rel=0.01)

    def test_local_vol_varies_by_time(self):
        d = _dupire()
        lv_t1 = d.local_vol(100.0, 0.5)
        lv_t2 = d.local_vol(100.0, 1.5)
        assert lv_t1 != lv_t2

    def test_local_vol_handles_low_strike(self):
        lv = _dupire().local_vol(0.1, 1.0)
        assert lv > 0
