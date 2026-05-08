import math
from datetime import datetime

import numpy as np
import scipy.sparse as sp
import scipy.sparse.linalg as spla

from neon.lib.core.constants import DATE_FORMAT
from neon.lib.instruments.options.option_type import OptionType


class LocalVolOption:
    """European option priced via Crank-Nicolson PDE with a DupireLocalVol surface."""

    def __init__(
        self,
        underlying_price: float,
        strike: float,
        risk_free_rate: float,
        current_date: str,
        expiry_date: str,
        option_type: OptionType,
        local_vol: object,
        n_spots: int = 200,
        n_steps: int = 100,
    ) -> None:
        self._S0 = underlying_price
        self._K = strike
        self._r = risk_free_rate
        self._T = _years_between(current_date, expiry_date)
        self._option_type = option_type
        self._local_vol = local_vol
        self._n_spots = n_spots
        self._n_steps = n_steps

    def price(self) -> float:
        S0, K, r, T = self._S0, self._K, self._r, self._T
        n, m = self._n_spots, self._n_steps

        S_max = S0 * 4.0
        dS = S_max / n
        dt = T / m

        # Spot grid (interior nodes 1..n-1; boundaries at 0 and S_max)
        S = np.linspace(0.0, S_max, n + 1)

        # Terminal payoff
        if self._option_type == OptionType.Call:
            V = np.maximum(S - K, 0.0)
        else:
            V = np.maximum(K - S, 0.0)

        interior = slice(1, n)

        for step in range(m):
            t = T - step * dt  # current time (counting backward from expiry)
            t_mid = max(t - 0.5 * dt, 1e-6)

            sigma = np.array([
                self._local_vol.local_vol(max(S[i], 1e-6), t_mid)
                for i in range(1, n)
            ])

            Si = S[interior]
            sig2 = sigma ** 2

            alpha = 0.25 * dt * (sig2 * (Si / dS) ** 2 - r * Si / dS)
            beta = -0.5 * dt * (sig2 * (Si / dS) ** 2 + r)
            gamma = 0.25 * dt * (sig2 * (Si / dS) ** 2 + r * Si / dS)

            diag = 1.0 - beta
            lower = -alpha[1:]
            upper = -gamma[:-1]
            A = sp.diags([lower, diag, upper], [-1, 0, 1], format="csc")

            rhs_diag = 1.0 + beta
            rhs_lower = alpha[1:]
            rhs_upper = gamma[:-1]
            B = sp.diags([rhs_lower, rhs_diag, rhs_upper], [-1, 0, 1], format="csc")

            rhs = B @ V[interior]

            # Boundary corrections
            if self._option_type == OptionType.Call:
                v_lo = 0.0
                v_hi = S_max - K * math.exp(-r * (t - dt))
            else:
                v_lo = K * math.exp(-r * (t - dt))
                v_hi = 0.0

            rhs[0] += alpha[0] * (v_lo + V[0])
            rhs[-1] += gamma[-1] * (v_hi + V[n])

            V_int = spla.spsolve(A, rhs)
            V[interior] = V_int
            V[0] = v_lo
            V[n] = v_hi

        # Interpolate at S0
        idx = int(S0 / dS)
        idx = min(max(idx, 0), n - 1)
        frac = (S0 - S[idx]) / dS
        return float(V[idx] * (1 - frac) + V[idx + 1] * frac)


def _years_between(d1: str, d2: str) -> float:
    t1 = datetime.strptime(d1, DATE_FORMAT)
    t2 = datetime.strptime(d2, DATE_FORMAT)
    return (t2 - t1).days / 365.0
