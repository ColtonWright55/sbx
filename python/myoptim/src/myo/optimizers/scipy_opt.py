import numpy as np
from scipy.optimize import minimize

from . import OptimizationResult


def optimize(func, bounds, budget=200, seed=None):
    rng = np.random.default_rng(seed)
    x0 = np.array([rng.uniform(lo, hi) for lo, hi in bounds])

    trajectory = []
    values = []

    def wrapped(x):
        v = func(x)
        trajectory.append(np.array(x, dtype=float))
        values.append(v)
        return v

    minimize(wrapped, x0, method="Nelder-Mead", bounds=bounds, options={"maxfev": budget})

    return OptimizationResult.from_history("scipy-nelder-mead", trajectory, values)
