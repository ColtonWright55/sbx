"""
Forward Euler vs backward Euler on three test problems.

    1. exponential decay             dy/dt = -y                    (mild)
    2. damped harmonic oscillator    2D linear system              (oscillatory, non-stiff)
    3. fast relaxation to forcing    dy/dt = -lambda*(y - cos t)   (very stiff, lambda = 1000)

Forward Euler is explicit and only conditionally stable: for problem 3 the
step size must stay below 2/lambda = 0.002 or the numerical solution
diverges. Backward Euler is implicit and stays bounded at step sizes that
wreck forward Euler, at the cost of a linear solve (here, a Newton solve)
per step.
"""

import numpy as np
import matplotlib.pyplot as plt

# ---------------------------------------------------------------- integrators
def forward_euler(f, y0, t):
    y = np.zeros((len(t), len(y0)))
    y[0] = y0
    for i in range(len(t) - 1):
        dt = t[i + 1] - t[i]
        y[i + 1] = y[i] + dt * f(t[i], y[i])
    return y


def backward_euler(f, y0, t, tol=1e-10, max_iter=20):
    n = len(y0)
    y = np.zeros((len(t), n))
    y[0] = y0
    eps = 1e-8
    for i in range(len(t) - 1):
        dt = t[i + 1] - t[i]
        tn1 = t[i + 1]
        yn1 = y[i].copy()                   # initial guess: previous point
        for _ in range(max_iter):
            F = yn1 - y[i] - dt * f(tn1, yn1)
            J = np.eye(n)
            for k in range(n):              # finite-difference Jacobian of F
                e = np.zeros(n)
                e[k] = eps
                J[:, k] -= dt * (f(tn1, yn1 + e) - f(tn1, yn1 - e)) / (2 * eps)
            step = np.linalg.solve(J, F)
            yn1 = yn1 - step
            if np.linalg.norm(step) < tol:
                break
        y[i + 1] = yn1
    return y


# ---------------------------------------------------------------- problem 1: exponential decay
# ODE:      dy/dt = -k*y,  y(0) = 1
# solution: y(t) = exp(-k*t)
k = 1.0
f1 = lambda t, y: np.array([-k * y[0]])
y1_0 = np.array([1.0])
y1_exact = lambda t: np.exp(-k * t)

# ---------------------------------------------------------------- problem 2: damped oscillator
# ODE:      x'' + 2*zeta*omega*x' + omega^2*x = 0,  x(0) = 1, x'(0) = 0
# solution: x(t) = exp(-zeta*omega*t) * (x0*cos(omega_d*t)
#               + ((v0 + zeta*omega*x0)/omega_d)*sin(omega_d*t)),  omega_d = omega*sqrt(1-zeta^2)
zeta, omega = 0.05, 5.0
def f2(t, y):
    x, v = y
    return np.array([v, -2 * zeta * omega * v - omega**2 * x])
y2_0 = np.array([1.0, 0.0])
omega_d = omega * np.sqrt(1 - zeta**2)
def y2_exact(t):
    return np.exp(-zeta * omega * t) * (
        y2_0[0] * np.cos(omega_d * t)
        + (y2_0[1] + zeta * omega * y2_0[0]) / omega_d * np.sin(omega_d * t)
    )

# ---------------------------------------------------------------- problem 3: stiff relaxation to forcing
# ODE:      dy/dt = -lambda*(y - cos(t)),  y(0) = 0
# solution: y(t) = -A*exp(-lambda*t) + A*cos(t) + B*sin(t),
#           A = lambda^2/(1+lambda^2), B = lambda/(1+lambda^2)
lam = 1000.0
f3 = lambda t, y: np.array([-lam * (y[0] - np.cos(t))])
y3_0 = np.array([0.0])
A = lam**2 / (1 + lam**2)
B = lam / (1 + lam**2)
y3_exact = lambda t: -A * np.exp(-lam * t) + A * np.cos(t) + B * np.sin(t)


# ---------------------------------------------------------------- run + plot
def compare(ax, f, y0, exact, t_end, dt, title, ylim=None):
    t = np.arange(0, t_end + dt / 2, dt)
    t_fine = np.linspace(0, t_end, 2000)
    y_fe = forward_euler(f, y0, t)
    y_be = backward_euler(f, y0, t)
    print(f"{title}: max |forward euler| = {np.max(np.abs(y_fe[:, 0])):.3e}, "
          f"max |backward euler| = {np.max(np.abs(y_be[:, 0])):.3e}")
    ax.plot(t_fine, exact(t_fine), "k-", lw=1.5, label="analytic")
    ax.plot(t, y_fe[:, 0], "o--", ms=3, label=f"forward euler (dt={dt})")
    ax.plot(t, y_be[:, 0], "s--", ms=3, label=f"backward euler (dt={dt})")
    ax.set_title(title)
    ax.set_xlabel("t")
    if ylim:
        ax.set_ylim(*ylim)
    ax.legend(fontsize=8)


# left column: dt inside forward Euler's stability region -- both methods
# agree and there's little reason to prefer backward Euler.
# right column: dt pushed past forward Euler's stability limit -- this is
# the regime backward Euler is actually for.
PROBLEMS = [
    dict(name="1. exponential decay, dy/dt = -y",
         f=f1, y0=y1_0, exact=y1_exact, t_end=8,
         dt_agree=0.2, dt_showcase=2.5, ylim_showcase=None),
    dict(name="2. damped oscillator",
         f=f2, y0=y2_0, exact=y2_exact, t_end=6,
         dt_agree=0.01, dt_showcase=0.3, ylim_showcase=(-10, 10)),
    dict(name="3. stiff: dy/dt = -1000 (y - cos t)",
         f=f3, y0=y3_0, exact=y3_exact, t_end=0.05,
         dt_agree=0.0005, dt_showcase=0.0025, ylim_showcase=(-10, 10)),
]

if __name__ == "__main__":
    fig, axes = plt.subplots(3, 2, figsize=(12, 11))
    for row, p in enumerate(PROBLEMS):
        compare(axes[row, 0], p["f"], p["y0"], p["exact"], p["t_end"], p["dt_agree"],
                title=f'{p["name"]}\ndt={p["dt_agree"]} (within stability limit)')
        compare(axes[row, 1], p["f"], p["y0"], p["exact"], p["t_end"], p["dt_showcase"],
                title=f'{p["name"]}\ndt={p["dt_showcase"]} (exceeds stability limit)',
                ylim=p["ylim_showcase"])

    axes[0, 0].annotate("forward & backward euler agree", xy=(0.5, 1.18),
                         xycoords="axes fraction", ha="center", fontsize=11, fontweight="bold")
    axes[0, 1].annotate("forward euler unstable, backward euler stays bounded", xy=(0.5, 1.18),
                         xycoords="axes fraction", ha="center", fontsize=11, fontweight="bold")

    plt.tight_layout()
    plt.show()
