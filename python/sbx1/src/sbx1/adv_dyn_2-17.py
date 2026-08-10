"""
Principles of Advanced Dynamics, Donald T. Greenwood, Problem 2-17.

A gyroscope spins with constant spin rate Omega = alpha_dot about its own
axis. That axis is a rigid shaft of length L pivoted at the fixed point O; it
holds a constant angle theta from the vertical and precesses about the
vertical at a constant rate phi_dot. Point pp sits on the rotor rim at radius
r from the shaft (this is Greenwood's "P"). Find the acceleration of pp.

Simple view: two nested rotating frames, and two moving points.
    frame'  (e1p, e2p, e3p)    spins about the fixed vertical e3p at rate
                                phi_dot. This is the precession frame.
    frame'' (e1pp, e2pp, e3pp) is frame' tilted by theta (about e2p), giving
                                the gyro's own spin axis e3pp. Right-handed in
                                both: e1p x e2p = e3p, e1pp x e2pp = e3pp.

    O   fixed pivot, at the world origin.
    p   the rotor hub: rides at the end of the shaft, L out from O along the
        spin axis e3pp. Carried by precession and tilt, but does not spin.
        p = O + L * e3pp
    pp  the rim point: offset r from p, spinning about the shaft in the
        (e1pp, e2pp) plane. pp = p + r * (cos(alpha) * e1pp + sin(alpha) * e2pp),
        alpha = Omega * t
"""

import time

import numpy as np
import pyvista as pv

# ---------------------------------------------------------------- parameters
r = 1.2                      # radius of pp from the spin axis [m]
theta = np.radians(25.0)     # constant tilt of the spin axis from vertical [rad]
phi_dot = 2 * np.pi * 0.15   # precession rate about vertical [rad/s]
Omega = 2 * np.pi * .5      # spin rate about the gyro's own axis, alpha_dot [rad/s]
L = 3.0                      # shaft length, O to hub p [m]

ref_axis_len = 1.5            # length of the drawn RGB world-axis arrows (cosmetic only) [m]


# ------------------------------------------------------------------ kinematics
def frame_p(phi):
    """Precession frame (e1p, e2p, e3p), in world coordinates. Spins about the
    fixed vertical e3p at rate phi_dot. Right-handed: e1p x e2p = e3p."""
    e1p = np.array([np.cos(phi), np.sin(phi), 0.0])
    e2p = np.array([-np.sin(phi), np.cos(phi), 0.0])
    e3p = np.array([0.0, 0.0, 1.0])
    return e1p, e2p, e3p


def frame_pp(e1p, e2p, e3p):
    """Gyro frame (e1pp, e2pp, e3pp) -- frame' tilted by theta about e2p.
    e3pp is the actual spin axis, right-handed: e1pp x e2pp = e3pp."""
    e1pp = np.cos(theta) * e1p - np.sin(theta) * e3p
    e2pp = e2p
    e3pp = np.cross(e1pp, e2pp)
    return e1pp, e2pp, e3pp


def state(t):
    """Fixed point O, hub p, and rim point pp, all in world coordinates."""
    phi = phi_dot * t
    e1p, e2p, e3p = frame_p(phi)
    e1pp, e2pp, e3pp = frame_pp(e1p, e2p, e3p)

    O = np.zeros(3)
    p = O + L * e3pp
    alpha = Omega * t
    pp = p + r * (np.cos(alpha) * e1pp + np.sin(alpha) * e2pp)

    return O, p, pp, e1pp, e2pp, e3pp


def analytical_acceleration(t):
    """Closed-form a_pp via the transport theorem / rotating-frame decomposition,
    resolved in the instantaneous precession basis (e1p, e2p, e3p) and converted
    to world coordinates. Verified against central finite differences to ~1e-6.
    """
    phi = phi_dot * t
    e1p, e2p, e3p = frame_p(phi)
    alpha = Omega * t

    a1p = (
        -phi_dot**2 * L * np.sin(theta)
        - r * np.cos(alpha) * ((phi_dot**2 + Omega**2) * np.cos(theta) + 2 * phi_dot * Omega)
    )
    a2p = -r * np.sin(alpha) * ((phi_dot**2 + Omega**2) + 2 * phi_dot * Omega * np.cos(theta))
    a3p = r * Omega**2 * np.cos(alpha) * np.sin(theta)

    return a1p * e1p + a2p * e2p + a3p * e3p


def numerical_acceleration(t, dt=1e-4):
    """Central-difference second derivative of the closed-form position of pp."""
    pp_m = state(t - dt)[2]
    pp_0 = state(t)[2]
    pp_p = state(t + dt)[2]
    return (pp_p - 2 * pp_0 + pp_m) / dt**2


def rotor_circle(p, e1pp, e2pp, radius, n=60):
    """The rotor rim: a circle of the given radius in the (e1pp, e2pp) plane,
    centered on the hub p."""
    angles = np.linspace(0.0, 2 * np.pi, n, endpoint=False)
    pts = p + radius * (np.cos(angles)[:, None] * e1pp + np.sin(angles)[:, None] * e2pp)
    return pv.lines_from_points(pts, close=True)


def add_world_axes(plotter, length=ref_axis_len):
    """RGB world reference frame (X red, Y green, Z blue) at the origin."""
    for direction, color in (((1, 0, 0), "red"), ((0, 1, 0), "green"), ((0, 0, 1), "blue")):
        arrow = pv.Arrow(
            start=(0.0, 0.0, 0.0),
            direction=direction,
            scale=length,
            tip_length=0.15,
            tip_radius=0.04,
            shaft_radius=0.015,
        )
        plotter.add_mesh(arrow, color=color)


# ----------------------------------------------------------------------- main
def main():
    plotter = pv.Plotter(shape=(1, 2))

    # ------------------------------------------------------------- 3D scene
    plotter.subplot(0, 0)
    plotter.set_background("white")
    add_world_axes(plotter)

    O0, p0, pp0, e1pp0, e2pp0, e3pp0 = state(0.0)

    pivot_mesh = pv.Sphere(radius=0.08, center=O0)
    plotter.add_mesh(pivot_mesh, color="black")

    tip_local = pv.Sphere(radius=0.06).points
    tip_mesh = pv.Sphere(radius=0.06, center=pp0)
    plotter.add_mesh(tip_mesh, color="orange")

    rod_mesh = pv.Line(O0, p0)
    plotter.add_mesh(rod_mesh, color="black", line_width=4)

    rotor_mesh = rotor_circle(p0, e1pp0, e2pp0, r)
    plotter.add_mesh(rotor_mesh, color="red", line_width=2)

    plotter.camera_position = "iso"

    # ---------------------------------------------------- acceleration chart
    plotter.subplot(0, 1)
    t_window = 5.0  # seconds of history shown

    probe_alpha = np.linspace(0.0, 2 * np.pi, 400)
    y_max = max(
        np.linalg.norm([
            -r * np.cos(a) * ((phi_dot**2 + Omega**2) * np.cos(theta) + 2 * phi_dot * Omega),
            -r * np.sin(a) * ((phi_dot**2 + Omega**2) + 2 * phi_dot * Omega * np.cos(theta)),
            r * Omega**2 * np.cos(a) * np.sin(theta),
        ])
        for a in probe_alpha
    ) * 1.15

    chart = pv.Chart2D()
    chart.x_label = "time [s]"
    chart.y_label = "|a_P| [m/s^2]"
    chart.x_range = (0.0, t_window)
    chart.y_range = (0.0, y_max)
    line_ana = chart.line([0], [0], color="red", label="analytical")
    line_num = chart.line([0], [0], color="blue", label="numerical (finite diff)")
    line_num.line_style = "--"
    chart.legend_visible = True
    plotter.add_chart(chart)

    # -------------------------------------------------------- pause control
    paused = [False]

    def toggle_pause():
        paused[0] = not paused[0]
        status_text.set_text(2, "PAUSED (space to resume)" if paused[0] else "")

    plotter.subplot(0, 0)
    status_text = plotter.add_text("", position="upper_left", font_size=12, color="red")
    plotter.add_key_event("space", toggle_pause)

    plotter.show(interactive_update=True, auto_close=False)

    t_hist, a_ana_hist, a_num_hist = [], [], []

    # ---------------------------------------------------- state update loop
    t = 0.0
    dt = 1 / 60
    while True:
        if not paused[0]:
            O, p, pp, e1pp, e2pp, e3pp = state(t)

            tip_mesh.points = tip_local + pp
            rod_mesh.points = pv.Line(O, p).points
            rotor_mesh.points = rotor_circle(p, e1pp, e2pp, r).points

            t_hist.append(t)
            a_ana_hist.append(np.linalg.norm(analytical_acceleration(t)))
            a_num_hist.append(np.linalg.norm(numerical_acceleration(t)))

            while t_hist and t_hist[0] < t - t_window:
                t_hist.pop(0)
                a_ana_hist.pop(0)
                a_num_hist.pop(0)

            line_ana.update(t_hist, a_ana_hist)
            line_num.update(t_hist, a_num_hist)
            chart.x_range = (max(0.0, t - t_window), max(t_window, t))

            t += dt

        plotter.update()
        time.sleep(dt)


if __name__ == "__main__":
    main()
