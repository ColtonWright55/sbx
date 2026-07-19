import benchmark_functions as bf

FUNCTIONS = {
    "rastrigin": lambda: bf.Rastrigin(n_dimensions=2),
    "ackley": lambda: bf.Ackley(n_dimensions=2),
    "beale": lambda: bf.Beale(),
    "schaffer2": lambda: bf.Schaffer2(),
}


def get_function(name):
    return FUNCTIONS[name]()


def bounds_list(func):
    lower, upper = func.suggested_bounds()
    return list(zip(lower, upper))
