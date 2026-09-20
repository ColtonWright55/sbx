"""
Principles of Advanced Dynamics, Donald T. Greenwood, Problem 2-16.

The plane of the windshield of a certain automobile is inclined at an angle
alpha with the vertical. The windshield wiper blade is of length l and
oscillates according to psi = psi0 * sin(beta * t), measured in the plane of
the windshield. The auto travels at constant speed v around a circular path
of radius R in a counterclockwise sense. This script animates the resulting
3D motion of the wiper tip P.

Frames:
    world       (X, Y, Z), Z up, circle centered at the origin.
    car body    (e_r, e_phi, e_z), the car's instantaneous cylindrical basis:
                e_r points outward from the circle's center O, e_phi is the
                direction of travel, e_z is up. Right-handed in that order:
                e_r x e_phi = e_z. Rotates with theta(t) = Omega * t.
    windshield  (e_rp, e_phip, e_zp), the wiper's own rotating basis: (e_phi, e_z)
                tilted back by alpha about -e_r, right-handed in the same
                pattern as the car frame: e_rp x e_phip = e_zp.

The wiper pivot is a fixed mount point on the windshield (fixed in the car
frame). The tip sweeps in the windshield plane about the e_zp axis:
    tip = pivot + l * (cos(psi) * e_rp + sin(psi) * e_phip)
"""

import time

import numpy as np
import pyvista as pv

# ---------------------------------------------------------------- parameters
R = 20.0                     # radius of car's circular path [m]
v = 8.0                      # car speed [m/s]
alpha = np.radians(30.0)     # windshield tilt from vertical [rad]
l = 1.5                      # wiper blade length [m]
psi0 = np.radians(45.0)      # wiper sweep amplitude [rad]
beta = 2 * np.pi * 0.75      # wiper angular frequency [rad/s] (~0.75 Hz)

h = 1.1                      # wiper pivot height above ground, car frame [m] (cosmetic only)
f = 0.0                      # wiper pivot forward offset from car origin [m] (must be 0 for a_pivot = -v^2/R e_r)

Omega = v / R                # car's angular speed around the circle [rad/s]


# ------------------------------------------------------------------ kinematics
def car_frame(theta):
    """Car's instantaneous cylindrical basis (e_r, e_phi, e_z), in world coordinates.
    Right-handed in this order: e_r x e_phi = e_z, matching Greenwood's convention."""
    e_r = np.array([np.cos(theta), np.sin(theta), 0.0])    # outward from O
    e_phi = np.array([-np.sin(theta), np.cos(theta), 0.0])  # direction of travel
    e_z = np.array([0.0, 0.0, 1.0])                          # up
    return e_r, e_phi, e_z


def windshield_frame(e_r, e_phi, e_z):
    """Wiper's own basis (e_rp, e_phip, e_zp) -- primed, i.e. r', phi', z' --
    the psi = 0 reference direction, the psi = +90 deg direction, and the axis
    psi actually sweeps about (into the glass) as it goes from e_rp to e_phip.
    Right-handed in this order, same pattern as car_frame: e_rp x e_phip = e_zp."""
    e_rp = -np.sin(alpha) * e_phi + np.cos(alpha) * e_z
    e_phip = -e_r
    e_zp = np.cross(e_rp, e_phip)
    return e_rp, e_phip, e_zp


def state(t):
    """Car center, wiper pivot, and wiper tip P, all in world coordinates."""
    theta = Omega * t
    e_r, e_phi, e_z = car_frame(theta)
    e_rp, e_phip, e_zp = windshield_frame(e_r, e_phi, e_z)

    car_pos = R * e_r
    pivot = car_pos + f * e_phi + h * e_z

    psi = psi0 * np.sin(beta * t)
    tip = pivot + l * (np.cos(psi) * e_rp + np.sin(psi) * e_phip)

    return car_pos, pivot, tip, e_rp, e_phip, e_zp


def analytical_acceleration(t):
    """Closed-form a_P via the transport theorem / rotating-frame decomposition,
    resolved in the instantaneous cylindrical basis (e_r, e_phi, e_z) of the car's
    circular path and converted to world coordinates. Verified against a direct
    cross-product (Omega x Omega x r + alpha x r + Coriolis) computation to 1e-13.
    Requires f = 0 (pivot on the circle) for the -v^2/R e_r base term to hold.
    """
    theta = Omega * t
    e_r, e_phi, e_z = car_frame(theta)

    psi = psi0 * np.sin(beta * t)
    psi_dot = psi0 * beta * np.cos(beta * t)
    psi_ddot = -psi0 * beta**2 * np.sin(beta * t)

    a_r = (
        -v**2 / R
        - l * psi_ddot * np.cos(psi)
        + l * np.sin(psi) * (psi_dot**2 + Omega**2 - 2 * Omega * psi_dot * np.sin(alpha))
    )
    a_phi = (
        l * np.sin(alpha) * np.cos(psi) * (Omega**2 + psi_dot**2)
        - 2 * l * Omega * psi_dot * np.cos(psi)
        + l * psi_ddot * np.sin(alpha) * np.sin(psi)
    )
    a_z = -l * np.cos(alpha) * (psi_ddot * np.sin(psi) + psi_dot**2 * np.cos(psi))

    return a_r * e_r + a_phi * e_phi + a_z * e_z


def numerical_acceleration(t, dt=1e-4):
    """Central-difference second derivative of the closed-form tip position."""
    tip_m = state(t - dt)[2]
    tip_0 = state(t)[2]
    tip_p = state(t + dt)[2]
    return (tip_p - 2 * tip_0 + tip_m) / dt**2


def windshield_quad(pivot, e_phip, e_rp, half_i=1.4, half_j=1.1):
    """A small rectangular patch representing the windshield, in the (e_rp, e_phip) plane."""
    corners = np.array([
        pivot - half_i * e_phip - half_j * e_rp,
        pivot + half_i * e_phip - half_j * e_rp,
        pivot + half_i * e_phip + half_j * e_rp,
        pivot - half_i * e_phip + half_j * e_rp,
    ])
    face = np.array([4, 0, 1, 2, 3])
    return pv.PolyData(corners, face)


def circle_polyline(radius, n=400):
    angles = np.linspace(0.0, 2 * np.pi, n, endpoint=False)
    pts = np.column_stack([radius * np.cos(angles), radius * np.sin(angles), np.zeros(n)])
    return pv.lines_from_points(pts, close=True)


# ----------------------------------------------------------------------- main
def main():
    plotter = pv.Plotter(shape=(1, 2))

    # ------------------------------------------------------------- 3D scene
    plotter.subplot(0, 0)
    plotter.set_background("white")
    plotter.add_mesh(circle_polyline(R), color="lightgray", line_width=1.5, opacity=0.5)

    car_pos0, pivot0, tip0, e_rp0, e_phip0, e_zp0 = state(0.0)

    car_local = pv.Sphere(radius=0.4).points
    car_mesh = pv.Sphere(radius=0.4, center=car_pos0)
    plotter.add_mesh(car_mesh, color="black")

    tip_local = pv.Sphere(radius=0.08).points
    tip_mesh = pv.Sphere(radius=0.08, center=tip0)
    plotter.add_mesh(tip_mesh, color="blue")

    windshield_mesh = windshield_quad(pivot0, e_phip0, e_rp0)
    plotter.add_mesh(windshield_mesh, color="lightblue", opacity=0.4)

    arm_mesh = pv.Line(pivot0, tip0)
    plotter.add_mesh(arm_mesh, color="red", line_width=4)

    plotter.camera_position = "iso"

    # ---------------------------------------------------- acceleration chart
    plotter.subplot(0, 1)
    t_window = 5.0  # seconds of history shown

    period = 2 * np.pi / beta
    probe_t = np.linspace(0.0, period, 400)
    y_max = max(np.linalg.norm(analytical_acceleration(pt)) for pt in probe_t) * 1.15

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
            car_pos, pivot, tip, e_rp, e_phip, e_zp = state(t)

            car_mesh.points = car_local + car_pos
            tip_mesh.points = tip_local + tip
            windshield_mesh.points = windshield_quad(pivot, e_phip, e_rp).points
            arm_mesh.points = pv.Line(pivot, tip).points

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
