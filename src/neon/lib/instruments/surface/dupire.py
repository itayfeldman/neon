import math
from datetime import date, datetime

from neon.lib.core.constants import DATE_FORMAT

_STRIKE_FLOOR = 1e-8


class DupireLocalVol:
    """Dupire local vol surface derived numerically from an SVISurface."""

    def __init__(self, surface: object, dK: float = 0.5, dT: float = 0.005) -> None:
        self._surface = surface
        self._dK = dK
        self._dT = dT
        self._min_strike = _STRIKE_FLOOR

    def _w(self, K: float, T: float) -> float:
        """Total implied variance at (K, T) via SVISurface."""
        expiry = self._T_to_expiry(T)
        iv = self._surface.get_vol(K, expiry)
        return iv * iv * T

    def _T_to_expiry(self, T: float) -> str:
        """Map time-to-expiry (years) to a DATE_FORMAT string for SVISurface lookup."""
        expiries = self._surface.expiries()
        times = [self._surface.time(e) for e in expiries]

        if T <= times[0]:
            return expiries[0]
        if T >= times[-1]:
            return expiries[-1]

        for i, expiry in enumerate(expiries):
            if times[i] == T:
                return expiry

        ordinals = [_str_to_ordinal(e) for e in expiries]
        for i in range(len(times) - 1):
            if times[i] <= T <= times[i + 1]:
                alpha = (T - times[i]) / (times[i + 1] - times[i])
                target_ord = round(
                    ordinals[i] + alpha * (ordinals[i + 1] - ordinals[i])
                )
                return date.fromordinal(target_ord).strftime(DATE_FORMAT)

        return expiries[-1]

    def local_vol(self, K: float, T: float) -> float:
        dK, dT = self._dK, self._dT
        K_clamped = max(K, self._min_strike)

        w = self._w(K_clamped, T)
        w_Kup = self._w(K_clamped + dK, T)
        K_dn = K_clamped - dK
        if K_dn >= self._min_strike:
            w_Kdn = self._w(K_dn, T)
            dw_dK = (w_Kup - w_Kdn) / (2 * dK)
            d2w_dK2 = (w_Kup - 2 * w + w_Kdn) / (dK ** 2)
        else:
            dw_dK = (w_Kup - w) / dK
            w_K2up = self._w(K_clamped + 2 * dK, T)
            d2w_dK2 = (w_K2up - 2 * w_Kup + w) / (dK ** 2)
        w_Tup = self._w(K_clamped, T + dT)

        dw_dT = (w_Tup - w) / dT

        F = self._forward(T)
        y = math.log(K_clamped / F) if F > 0 else 0.0

        if w <= 0 or dw_dT <= 0:
            return float(self._surface.get_vol(K_clamped, self._T_to_expiry(T)))

        denom = (
            1.0
            - (y / w) * dw_dK
            + 0.25 * (-0.25 - 1.0 / w + y ** 2 / w ** 2) * dw_dK ** 2
            + 0.5 * d2w_dK2
        )
        if denom <= 0:
            return float(self._surface.get_vol(K_clamped, self._T_to_expiry(T)))

        loc_var = dw_dT / denom
        return float(math.sqrt(max(loc_var, 1e-8)))

    def _forward(self, T: float) -> float:
        expiry = self._T_to_expiry(T)
        expiries = self._surface.expiries()
        if expiry in expiries:
            return self._surface.forward(expiry)
        times = [self._surface.time(e) for e in expiries]
        fwds = [self._surface.forward(e) for e in expiries]
        if T <= times[0]:
            return fwds[0]
        if T >= times[-1]:
            return fwds[-1]
        for i in range(len(times) - 1):
            if times[i] <= T <= times[i + 1]:
                alpha = (T - times[i]) / (times[i + 1] - times[i])
                return fwds[i] + alpha * (fwds[i + 1] - fwds[i])
        return fwds[-1]


def _str_to_ordinal(date_str: str) -> int:
    return datetime.strptime(date_str, DATE_FORMAT).toordinal()
