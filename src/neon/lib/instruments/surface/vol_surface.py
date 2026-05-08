from datetime import datetime

import numpy as np
from scipy.interpolate import RegularGridInterpolator

from neon.lib.core.constants import DATE_FORMAT


class VolatilitySurface:
    def __init__(
        self,
        strikes: list[float],
        expiries: list[str],
        vols: list[list[float]],
    ) -> None:
        self._strikes = np.array(strikes, dtype=float)
        self._expiry_days = np.array(
            [self._to_days(e) for e in expiries], dtype=float
        )
        self._interpolator = RegularGridInterpolator(
            (self._strikes, self._expiry_days),
            np.array(vols, dtype=float),
            method="linear",
            bounds_error=False,
            fill_value=None,
        )

    def get_vol(self, strike: float, expiry: str) -> float:
        strike = float(np.clip(strike, self._strikes[0], self._strikes[-1]))
        raw_days = self._to_days(expiry)
        days = float(np.clip(raw_days, self._expiry_days[0], self._expiry_days[-1]))
        return float(self._interpolator([[strike, days]])[0])

    @staticmethod
    def _to_days(date_str: str) -> float:
        return float(datetime.strptime(date_str, DATE_FORMAT).toordinal())
