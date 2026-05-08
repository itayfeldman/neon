from collections.abc import Callable

import numpy as np


def simulate_gbm(
    S: float,
    r: float,
    sigma: float,
    T: float,
    steps: int,
    n_sim: int,
) -> np.ndarray:
    dt = T / steps
    drift = (r - 0.5 * sigma**2) * dt
    diffusion = sigma * np.sqrt(dt)
    Z = np.random.standard_normal((n_sim, steps))
    log_returns = drift + diffusion * Z
    paths = np.empty((n_sim, steps + 1))
    paths[:, 0] = S
    np.exp(log_returns, out=paths[:, 1:])
    np.cumprod(paths[:, 1:], axis=1, out=paths[:, 1:])
    paths[:, 1:] *= S
    return paths


def price_mc(
    paths: np.ndarray,
    payoff_fn: Callable[[np.ndarray], np.ndarray],
    r: float,
    T: float,
) -> float:
    return float(np.exp(-r * T) * np.mean(payoff_fn(paths)))
