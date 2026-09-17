"""
Linear Kalman filter on a linearized pendulum, tracking the true nonlinear
pendulum through noisy angle measurements.

    true plant (simulated):  theta'' = -(g/L) sin(theta) - c*theta'
    filter's model:          theta'' = -(g/L) theta        - c*theta'   (sin(theta) ~ theta)

The filter never sees the true nonlinear plant -- it only gets noisy angle
measurements z_k = theta_true(t_k) + v_k and propagates its belief with the
linearized, constant-coefficient F matrix. Two initial amplitudes are run:
small (linearization is accurate, sin(theta) ~ theta) and large (linearization
breaks down, sin(theta) far from theta). For each, three trajectories are
compared against the true nonlinear angle:

    1. open-loop linear model, no measurement updates (pure model drift)
    2. Kalman filter, fusing noisy measurements into the same linear model
    3. the noisy measurements themselves

This isolates two error sources: sensor noise (which the KF suppresses) and
linearization/model error (which the KF cannot fully correct, since a
constant-coefficient KF has no way to represent the amplitude-dependent
restoring force of sin(theta)).
"""

import matplotlib.pyplot as plt
import numpy as np

g = 9.81
L = 1.0
c = 0.15


def pendulum_deriv(state):
    theta, omega = state
    return np.array([omega, -(g / L) * np.sin(theta) - c * omega])


def rk4_step(f, x, dt):
    k1 = f(x)
    k2 = f(x + dt / 2 * k1)
    k3 = f(x + dt / 2 * k2)
    k4 = f(x + dt * k3)
    return x + dt / 6 * (k1 + 2 * k2 + 2 * k3 + k4)


def simulate_nonlinear(x0, t):
    x = np.zeros((len(t), 2))
    x[0] = x0
    for k in range(len(t) - 1):
        x[k + 1] = rk4_step(pendulum_deriv, x[k], t[k + 1] - t[k])
    return x


def linearized_F(dt):
    return np.array([[1.0, dt], [-(g / L) * dt, 1.0 - c * dt]])


def simulate_linear_open_loop(x0, t):
    F = linearized_F(t[1] - t[0])
    x = np.zeros((len(t), 2))
    x[0] = x0
    for k in range(len(t) - 1):
        x[k + 1] = F @ x[k]
    return x


def kalman_filter(z, dt, Q, R, x0, P0):
    F = linearized_F(dt)
    h = np.array([1.0, 0.0])
    n = len(z)
    x_est = np.zeros((n, 2))
    P_diag = np.zeros((n, 2))
    x = x0.copy()
    P = P0.copy()
    for k in range(n):
        if k > 0:
            x = F @ x
            P = F @ P @ F.T + Q
        S = h @ P @ h + R
        K = (P @ h) / S
        x = x + K * (z[k] - h @ x)
        P = P - np.outer(K, h) @ P
        x_est[k] = x
        P_diag[k] = np.diag(P)
    return x_est, P_diag


def rmse(a, b):
    return np.sqrt(np.mean((a - b) ** 2))


def run_case(ax_theta, ax_err, theta0_deg, rng):
    dt = 0.01
    t = np.arange(0, 10 + dt / 2, dt)
    x0 = np.array([np.deg2rad(theta0_deg), 0.0])

    x_true = simulate_nonlinear(x0, t)
    x_lin = simulate_linear_open_loop(x0, t)

    meas_std = 0.05
    z = x_true[:, 0] + rng.normal(0.0, meas_std, len(t))

    Q = np.diag([1e-7, 1e-5])
    R = meas_std**2
    P0 = np.diag([0.01, 0.01])
    x_kf, P_kf = kalman_filter(z, dt, Q, R, x0, P0)

    ax_theta.plot(t, np.rad2deg(z), ".", ms=1.5, color="0.75", label="noisy measurement")
    ax_theta.plot(t, np.rad2deg(x_true[:, 0]), "k-", lw=1.6, label="true (nonlinear)")
    ax_theta.plot(t, np.rad2deg(x_lin[:, 0]), "--", lw=1.2, label="linear model (open-loop)")
    ax_theta.plot(t, np.rad2deg(x_kf[:, 0]), "-", lw=1.2, label="Kalman filter estimate")
    ax_theta.set_title(f"theta0 = {theta0_deg} deg")
    ax_theta.set_xlabel("t [s]")
    ax_theta.set_ylabel("theta [deg]")
    ax_theta.legend(fontsize=7, loc="upper right")

    err_lin = np.rad2deg(x_lin[:, 0] - x_true[:, 0])
    err_kf = np.rad2deg(x_kf[:, 0] - x_true[:, 0])
    sigma = np.rad2deg(np.sqrt(P_kf[:, 0]))
    ax_err.plot(t, err_lin, "--", lw=1.0, label=f"open-loop error (rmse={rmse(x_lin[:, 0], x_true[:, 0]):.4f} rad)")
    ax_err.plot(t, err_kf, "-", lw=1.0, label=f"KF error (rmse={rmse(x_kf[:, 0], x_true[:, 0]):.4f} rad)")
    ax_err.fill_between(t, -3 * sigma, 3 * sigma, color="C1", alpha=0.15, label="KF +/-3 sigma")
    ax_err.axhline(0, color="k", lw=0.6)
    ax_err.set_xlabel("t [s]")
    ax_err.set_ylabel("theta error [deg]")
    ax_err.legend(fontsize=7, loc="upper right")

    print(
        f"theta0={theta0_deg:>4} deg  "
        f"open-loop rmse={rmse(x_lin[:, 0], x_true[:, 0]):.5f} rad  "
        f"KF rmse={rmse(x_kf[:, 0], x_true[:, 0]):.5f} rad"
    )


if __name__ == "__main__":
    rng = np.random.default_rng(0)
    fig, axes = plt.subplots(2, 2, figsize=(12, 8))
    run_case(axes[0, 0], axes[0, 1], theta0_deg=10, rng=rng)
    run_case(axes[1, 0], axes[1, 1], theta0_deg=150, rng=rng)
    fig.suptitle("Linear KF on a linearized pendulum vs. true nonlinear pendulum", fontweight="bold")
    plt.tight_layout()
    plt.show()
