"""
Explore "excess curvature" ideas.

If we have two perturbed bubbles and a mapping between them, we can compute the difference in curvature. This could be
useful for penalizing a forging controller, certainly you would not penalize curvature that is entirely necessary.
"""

import numpy as np
import pyvista as pv
import open3d as o3d

from diffgeo1 import *

def plot_delta_curvatures_pb(pb1, pb2, K1, K2, H1, H2, opacity=0.2):
    """
    Renders two perturbed bubble surfaces together: pb2 as a translucent,
    grayed-out reference shell, and pb1 colormapped by the excess curvature
    (K2 - K1, H2 - H1) at each shared (u, v) parameter coordinate.

    Parameters:
    pb1, pb2 (tuple of ndarray): (X, Y, Z) coordinates from perturbed_bubble,
        both sampled on the same (u, v) grid.
    K1, K2, H1, H2 (ndarray): Gaussian and mean curvatures of pb1 and pb2,
        evaluated at that same (u, v) grid.
    opacity (float): opacity of the grayed-out pb2 reference shell.
    """
    grid1 = pv.StructuredGrid(*pb1)
    grid1["dK"] = (K2 - K1).ravel(order="F")
    grid1["dH"] = (H2 - H1).ravel(order="F")

    grid2 = pv.StructuredGrid(*pb2)

    for scalars in ("dK", "dH"):
        clim = np.nanpercentile(grid1[scalars], [25, 75])

        plotter = pv.Plotter(lighting="three lights")
        plotter.enable_anti_aliasing("fxaa")
        plotter.add_mesh(
            grid2,
            color="gray",
            opacity=opacity,
            smooth_shading=True,
        )
        plotter.add_mesh(
            grid1,
            scalars=scalars,
            cmap="viridis",
            clim=clim,
            smooth_shading=True,
            specular=0.5,
            specular_power=15,
        )
        plotter.show_grid()
        plotter.add_axes()
        plotter.add_text(scalars, font_size=12)
        plotter.show()


def main():
    R0 = 1.0
    m1, n1 = 8, 2
    m2, n2 = 4, 2
    density = 1000

    u = np.linspace(0, np.pi, density)
    v = np.linspace(0, 2 * np.pi, density)
    u, v = np.meshgrid(u, v)

    A1, A2 = 0.10, 0.10

    pb1 = perturbed_bubble(u, v, R0, A1, m1, n1)
    pb2 = perturbed_bubble(u, v, R0, A2, m2, n2)

    K1, H1 = curvatures_pb(u, v, R0, A1, m1, n1)
    K2, H2 = curvatures_pb(u, v, R0, A2, m2, n2)

    plot_delta_curvatures_pb(pb1, pb2, K1, K2, H1, H2)


if __name__ == "__main__":
    main()
