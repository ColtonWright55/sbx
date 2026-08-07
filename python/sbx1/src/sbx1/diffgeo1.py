import numpy as np
import pyvista as pv

def perturbed_bubble(u, v, R0, A, m, n):
    """
    Generates a perturbed bubble surface based on the given parameters.

    Parameters:
    u (ndarray): The u parameter grid.
    v (ndarray): The v parameter grid.
    R0 (float): Base radius of the bubble.
    A (float): Amplitude of the perturbation.
    m (int): Frequency of the perturbation in the u direction.
    n (int): Frequency of the perturbation in the v direction.

    Returns:
    X, Y, Z (ndarray): Coordinates of the perturbed bubble surface.
    """
    r = R0 + A * np.sin(n * u) * np.cos( m * v)
    X = r * np.sin(u) * np.cos(v)
    Y = r * np.sin(u) * np.sin(v)
    Z = r * np.cos(u)

    return X, Y, Z


def plot_perturbed_bubble(R0=1.0, A=0.35, m=6, n=8, density=1000):
    """
    Renders the perturbed bubble surface with PyVista at very high mesh density.

    Parameters:
    R0, A, m, n: passed through to perturbed_bubble.
    density (int): number of samples along each of u and v (density x density mesh).
    """
    u = np.linspace(0, np.pi, density)
    v = np.linspace(0, 2 * np.pi, density)
    u, v = np.meshgrid(u, v)

    X, Y, Z = perturbed_bubble(u, v, R0, A, m, n)
    r = np.sqrt(X**2 + Y**2 + Z**2)

    grid = pv.StructuredGrid(X, Y, Z)
    grid["radius"] = r.ravel(order="F")

    plotter = pv.Plotter(lighting="three lights")
    plotter.enable_anti_aliasing("fxaa")
    plotter.add_mesh(
        grid,
        scalars="radius",
        cmap="viridis",
        smooth_shading=True,
        specular=0.5,
        specular_power=15,
    )
    plotter.show_grid()
    plotter.add_axes()
    plotter.show()


def main():
    plot_perturbed_bubble(A=0.10, m=15, n=2, density=1000)

if __name__ == "__main__":
    main()
