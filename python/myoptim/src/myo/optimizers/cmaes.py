from . import OptimizationResult


def optimize(func, bounds, budget=200, seed=None):
    import cma

    lower = [b[0] for b in bounds]
    upper = [b[1] for b in bounds]
    x0 = [(lo + hi) / 2 for lo, hi in bounds]
    sigma0 = min(hi - lo for lo, hi in bounds) / 4

    es = cma.CMAEvolutionStrategy(
        x0,
        sigma0,
        {"bounds": [lower, upper], "maxfevals": budget, "seed": seed or 0, "verbose": -9},
    )

    trajectory = []
    values = []
    while not es.stop():
        solutions = es.ask()
        fitnesses = [func(x) for x in solutions]
        es.tell(solutions, fitnesses)
        trajectory.extend(solutions)
        values.extend(fitnesses)

    return OptimizationResult.from_history("cma-es", trajectory, values)
