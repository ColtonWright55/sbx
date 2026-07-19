import argparse

from .. import viz
from ..functions import bounds_list, get_function

OPTIMIZERS = {
    "scipy": "myo.optimizers.scipy_opt",
    "cmaes": "myo.optimizers.cmaes",
    "botorch": "myo.optimizers.botorch_opt",
}


def run_optimizer(name, func, bounds, budget, seed):
    import importlib

    module = importlib.import_module(OPTIMIZERS[name])
    return module.optimize(func, bounds, budget=budget, seed=seed)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("function", choices=["rastrigin", "ackley", "beale", "schaffer2"])
    parser.add_argument("optimizer", choices=list(OPTIMIZERS))
    parser.add_argument("--budget", type=int, default=200)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--backend", choices=["plotly", "pyvista"], default="plotly")
    args = parser.parse_args()

    func = get_function(args.function)
    bounds = bounds_list(func)
    result = run_optimizer(args.optimizer, func, bounds, args.budget, args.seed)

    print(f"{result.name}: best={result.best_value:.5f} at {result.best_point}")

    if args.backend == "plotly":
        viz.plot_plotly(func, result=result)
    else:
        viz.plot_pyvista(func, result=result)


if __name__ == "__main__":
    main()
