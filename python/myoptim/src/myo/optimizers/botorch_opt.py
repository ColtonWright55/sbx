from . import OptimizationResult


def optimize(func, bounds, budget=200, seed=None, n_init=10):
    import torch
    from botorch.acquisition import LogExpectedImprovement
    from botorch.fit import fit_gpytorch_mll
    from botorch.models import SingleTaskGP
    from botorch.optim import optimize_acqf
    from botorch.utils.transforms import unnormalize
    from gpytorch.mlls import ExactMarginalLogLikelihood

    torch.manual_seed(seed or 0)
    dim = len(bounds)
    lower = torch.tensor([b[0] for b in bounds], dtype=torch.double)
    upper = torch.tensor([b[1] for b in bounds], dtype=torch.double)
    bounds_t = torch.stack([lower, upper])
    unit_bounds = torch.stack([torch.zeros(dim, dtype=torch.double), torch.ones(dim, dtype=torch.double)])

    def evaluate(x_unit):
        x_real = unnormalize(x_unit, bounds_t)
        return torch.tensor(
            [func(x.tolist()) for x in x_real], dtype=torch.double
        ).unsqueeze(-1)

    train_x = torch.rand(n_init, dim, dtype=torch.double)  # already in [0, 1]
    train_y = evaluate(train_x)

    for _ in range(budget - n_init):
        # botorch maximizes; we're minimizing func, so feed it the negated values
        model = SingleTaskGP(train_x, -train_y)
        mll = ExactMarginalLogLikelihood(model.likelihood, model)
        fit_gpytorch_mll(mll)

        acqf = LogExpectedImprovement(model, best_f=(-train_y).max())
        candidate, _ = optimize_acqf(acqf, bounds=unit_bounds, q=1, num_restarts=5, raw_samples=64)

        new_y = evaluate(candidate)
        train_x = torch.cat([train_x, candidate])
        train_y = torch.cat([train_y, new_y])

    train_x_real = unnormalize(train_x, bounds_t)
    return OptimizationResult.from_history(
        "botorch-ei", train_x_real.numpy(), train_y.numpy().ravel(), n_init=n_init
    )
