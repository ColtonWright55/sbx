from dataclasses import dataclass

import numpy as np


@dataclass
class OptimizationResult:
    name: str
    trajectory: np.ndarray  # shape (n_evals, n_dims), every point evaluated
    values: np.ndarray  # shape (n_evals,)
    best_point: np.ndarray
    best_value: float
    n_init: int = 0  # leading points that were random/space-filling, not optimizer-chosen

    @classmethod
    def from_history(cls, name, trajectory, values, n_init=0):
        trajectory = np.asarray(trajectory, dtype=float)
        values = np.asarray(values, dtype=float)
        best_idx = int(np.argmin(values))
        return cls(
            name=name,
            trajectory=trajectory,
            values=values,
            best_point=trajectory[best_idx],
            best_value=values[best_idx],
            n_init=n_init,
        )
