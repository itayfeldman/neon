import pytest

from neon.lib.instruments.surface.vol_surface import VolatilitySurface

STRIKES = [90.0, 100.0, 110.0]
EXPIRIES = ["20260101", "20260701", "20270101"]
VOLS = [
    [0.25, 0.22, 0.20],  # strike=90
    [0.20, 0.18, 0.17],  # strike=100
    [0.22, 0.20, 0.19],  # strike=110
]


def _surface() -> VolatilitySurface:
    return VolatilitySurface(strikes=STRIKES, expiries=EXPIRIES, vols=VOLS)


# ---------------------------------------------------------------------------
# Exact grid lookups
# ---------------------------------------------------------------------------


class TestExactLookup:
    @pytest.mark.parametrize("si,ei", [(i, j) for i in range(3) for j in range(3)])
    def test_grid_point_returns_stored_vol(self, si, ei):
        surf = _surface()
        result = surf.get_vol(STRIKES[si], EXPIRIES[ei])
        assert result == pytest.approx(VOLS[si][ei], abs=1e-10)

    def test_returns_float(self):
        surf = _surface()
        assert isinstance(surf.get_vol(100.0, "20260101"), float)


# ---------------------------------------------------------------------------
# Interpolation
# ---------------------------------------------------------------------------


class TestInterpolation:
    def test_mid_strike_between_boundaries(self):
        surf = _surface()
        vol = surf.get_vol(95.0, "20260101")
        lo = surf.get_vol(90.0, "20260101")
        hi = surf.get_vol(100.0, "20260101")
        assert lo >= vol >= hi or lo <= vol <= hi

    def test_mid_expiry_between_boundaries(self):
        surf = _surface()
        # Midpoint between "20260101" and "20260701"
        vol = surf.get_vol(100.0, "20260401")
        lo = surf.get_vol(100.0, "20260101")
        hi = surf.get_vol(100.0, "20260701")
        assert min(lo, hi) <= vol <= max(lo, hi)

    def test_bilinear_interpolation_midpoint(self):
        surf = _surface()
        # Midpoint of strike range → average of the two boundary vols
        mid_vol = surf.get_vol(95.0, "20260101")
        expected = (VOLS[0][0] + VOLS[1][0]) / 2
        assert mid_vol == pytest.approx(expected, abs=1e-6)


# ---------------------------------------------------------------------------
# Out-of-range clamping (no NaN, no exception)
# ---------------------------------------------------------------------------


class TestClamping:
    def test_strike_below_range_clamps(self):
        surf = _surface()
        result = surf.get_vol(50.0, "20260101")
        assert isinstance(result, float)
        assert not (result != result)  # not NaN

    def test_strike_above_range_clamps(self):
        surf = _surface()
        result = surf.get_vol(200.0, "20260101")
        assert isinstance(result, float)
        assert not (result != result)

    def test_expiry_before_range_clamps(self):
        surf = _surface()
        result = surf.get_vol(100.0, "20200101")
        assert isinstance(result, float)
        assert not (result != result)

    def test_expiry_after_range_clamps(self):
        surf = _surface()
        result = surf.get_vol(100.0, "20991231")
        assert isinstance(result, float)
        assert not (result != result)

    def test_clamped_strike_equals_boundary(self):
        surf = _surface()
        # Deep OTM should return same as the boundary strike
        assert surf.get_vol(50.0, "20260101") == pytest.approx(
            surf.get_vol(90.0, "20260101"), abs=1e-10
        )

    def test_clamped_high_strike_equals_boundary(self):
        surf = _surface()
        assert surf.get_vol(500.0, "20260101") == pytest.approx(
            surf.get_vol(110.0, "20260101"), abs=1e-10
        )
