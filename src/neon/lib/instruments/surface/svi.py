import math
from dataclasses import dataclass
from datetime import datetime

import numpy as np
from scipy.optimize import minimize

from neon.lib.core.constants import DATE_FORMAT


def _to_ordinal(date_str: str) -> int:
    return datetime.strptime(date_str, DATE_FORMAT).toordinal()


@dataclass
class SVISlice:
    a: float
    b: float
    rho: float
    m: float
    sigma: float

    def total_variance(self, k: float, forward: float) -> float:
        lm = math.log(k / forward)
        return self.a + self.b * (
            self.rho * (lm - self.m) + math.sqrt((lm - self.m) ** 2 + self.sigma ** 2)
        )

    def implied_vol(self, k: float, forward: float, T: float) -> float:
        return float(math.sqrt(max(self.total_variance(k, forward), 0.0) / T))


class SVICalibrator:
    @staticmethod
    def fit(
        strikes: list[float],
        forward: float,
        T: float,
        market_vols: list[float],
    ) -> SVISlice:
        strikes_arr = np.array(strikes, dtype=float)
        market_arr = np.array(market_vols, dtype=float)
        atm_var = float(np.mean(market_arr)) ** 2 * T

        x0 = [atm_var * 0.5, 0.1, -0.3, 0.0, 0.2]
        bounds = [
            (-10.0, 10.0),   # a
            (1e-4, 2.0),     # b
            (-0.999, 0.999), # rho
            (-2.0, 2.0),     # m
            (1e-4, 2.0),     # sigma
        ]

        def objective(x: np.ndarray) -> float:
            sl = SVISlice(*x)
            fitted = np.array([sl.implied_vol(k, forward, T) for k in strikes_arr])
            return float(np.sum((fitted - market_arr) ** 2))

        result = minimize(objective, x0, method="L-BFGS-B", bounds=bounds)
        return SVISlice(*result.x)


class SVISurface:
    def __init__(
        self,
        slices: dict[str, SVISlice],
        forwards: dict[str, float],
        times: dict[str, float],
    ) -> None:
        self._slices = slices
        self._forwards = forwards
        self._times = times
        self._expiries = sorted(slices.keys())

    def expiries(self) -> tuple[str, ...]:
        return tuple(self._expiries)

    def forward(self, expiry: str) -> float:
        return self._forwards[expiry]

    def time(self, expiry: str) -> float:
        return self._times[expiry]

    @classmethod
    def calibrate(
        cls,
        market_data: dict[str, tuple[list[float], list[float]]],
        forwards: dict[str, float] | None = None,
        times: dict[str, float] | None = None,
    ) -> "SVISurface":
        slices: dict[str, SVISlice] = {}
        fwds: dict[str, float] = {}
        ts: dict[str, float] = {}
        for expiry, (strikes, vols) in market_data.items():
            F = forwards[expiry] if forwards else 100.0
            T = times[expiry] if times else 1.0
            slices[expiry] = SVICalibrator.fit(strikes, F, T, vols)
            fwds[expiry] = F
            ts[expiry] = T
        return cls(slices, fwds, ts)

    def _slice_vol(self, strike: float, expiry: str) -> float:
        sl = self._slices[expiry]
        return sl.implied_vol(strike, self._forwards[expiry], self._times[expiry])

    def get_vol(self, strike: float, expiry: str) -> float:
        if expiry in self._slices:
            return self._slice_vol(strike, expiry)
        expiries = self._expiries
        if expiry <= expiries[0]:
            return self._slice_vol(strike, expiries[0])
        if expiry >= expiries[-1]:
            return self._slice_vol(strike, expiries[-1])
        for i in range(len(expiries) - 1):
            e1, e2 = expiries[i], expiries[i + 1]
            if e1 <= expiry <= e2:
                t1, t2 = self._times[e1], self._times[e2]
                w1 = self._slices[e1].total_variance(strike, self._forwards[e1])
                w2 = self._slices[e2].total_variance(strike, self._forwards[e2])
                d1, d2, d = _to_ordinal(e1), _to_ordinal(e2), _to_ordinal(expiry)
                alpha = (d - d1) / (d2 - d1)
                w = w1 + alpha * (w2 - w1)
                T = t1 + alpha * (t2 - t1)
                return float(math.sqrt(max(w, 0.0) / T))
        return self._slice_vol(strike, expiries[-1])
