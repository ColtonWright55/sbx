import numpy as np
import pyvista as pv
import open3d as o3d

def perturbed_bubble(u, v, R0, A, m, n):
    """
    Generates a perturbed bubble surface.

    Parameters:
    u (ndarray): Polar/colatitude angle, measured from the +Z axis (north pole),
        range [0, pi].
    v (ndarray): Azimuthal angle, measured from the +X axis within the XY-plane,
        increasing toward +Y, range [0, 2*pi].
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

def grad_pb(u, v, R0, A, m, n):
    """
    Computes the analytical gradient of the perturbed bubble surface.

    Parameters:
    u (ndarray): The u parameter grid.
    v (ndarray): The v parameter grid.
    R0 (float): Base radius of the bubble.
    A (float): Amplitude of the perturbation.
    m (int): Frequency of the perturbation in the u direction.
    n (int): Frequency of the perturbation in the v direction.

    Returns:
    J, N (ndarray): The Jacobian and normal vectors of the perturbed bubble surface.
    """
    r = R0 + A * np.sin(n * u) * np.cos(m * v)
    
    dr_du = A * n * np.cos(n * u) * np.cos(m * v)
    dr_dv = -A * m * np.sin(n * u) * np.sin(m * v)

    dx_du = dr_du * np.sin(u) * np.cos(v) + r * np.cos(u) * np.cos(v)
    dy_du = dr_du * np.sin(u) * np.sin(v) + r * np.cos(u) * np.sin(v)
    dz_du = dr_du * np.cos(u) - r * np.sin(u)

    dx_dv = dr_dv * np.sin(u) * np.cos(v) - r * np.sin(u) * np.sin(v)
    dy_dv = dr_dv * np.sin(u) * np.sin(v) + r * np.sin(u) * np.cos(v)
    dz_dv = dr_dv * np.cos(u)

    Xu = np.stack([dx_du, dy_du, dz_du], axis=-1)
    Yv = np.stack([dx_dv, dy_dv, dz_dv], axis=-1)
    J = np.stack([Xu, Yv], axis=-2)

    N = np.cross(Xu, Yv)
    N /= np.linalg.norm(N, axis=-1, keepdims=True)

    return J, N



def plot_perturbed_bubble(R0=1.0, A=0.35, m=6, n=8, density=1000,
                           slice_u=None, slice_density=1000, arrow_mag=0.01,
                           all_normals=False, all_normals_density=40):
    """
    Renders the perturbed bubble surface with PyVista.

    Parameters:
    R0, A, m, n: passed through to perturbed_bubble.
    density (int): number of samples along each of u and v (density x density mesh).
    slice_u (float or None): u value at which to draw a ring of surface normals
        (holding u constant, sweeping v). Set to None to skip.
    slice_density (int): number of normal vectors drawn around the slice.
    arrow_mag (float): length scale of the plotted normal arrows.
    all_normals (bool): if True, draw normal vectors over the whole surface
        (every u and v), on a coarser grid than the mesh density.
    all_normals_density (int): number of samples along each of u and v for the
        all_normals arrow grid.
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

    if slice_u is not None:
        v_slice = np.linspace(0, 2 * np.pi, slice_density, endpoint=False)
        u_slice = np.full_like(v_slice, slice_u)

        Xs, Ys, Zs = perturbed_bubble(u_slice, v_slice, R0, A, m, n)
        _, Ns = grad_pb(u_slice, v_slice, R0, A, m, n)

        points = np.stack([Xs, Ys, Zs], axis=-1)
        plotter.add_arrows(points, Ns, mag=arrow_mag, color="red")

    if all_normals:
        ua = np.linspace(0, np.pi, all_normals_density)
        va = np.linspace(0, 2 * np.pi, all_normals_density, endpoint=False)
        ua, va = np.meshgrid(ua, va)

        Xa, Ya, Za = perturbed_bubble(ua, va, R0, A, m, n)
        _, Na = grad_pb(ua, va, R0, A, m, n)

        points = np.stack([Xa, Ya, Za], axis=-1).reshape(-1, 3)
        Na = Na.reshape(-1, 3)
        plotter.add_arrows(points, Na, mag=arrow_mag, color="red")

    plotter.show_grid()
    plotter.add_axes()
    plotter.show()


def plot_point_cloud_o3d(R0=1.0, A=0.35, m=6, n=8, density=200, k_neighbors=30):
    """
    Samples the perturbed bubble surface into a raw point cloud, hands it to
    Open3D, and runs Open3D's PCA-based normal estimation.

    Parameters:
    R0, A, m, n: passed through to perturbed_bubble.
    density (int): number of samples along each of u and v (density x density points).
    k_neighbors (int): neighborhood size used by Open3D for normal estimation
        and for making normal orientation locally consistent.
    """
    u = np.linspace(0, np.pi, density)
    v = np.linspace(0, 2 * np.pi, density, endpoint=False)
    u, v = np.meshgrid(u, v)

    X, Y, Z = perturbed_bubble(u, v, R0, A, m, n)
    points = np.stack([X, Y, Z], axis=-1).reshape(-1, 3)

    pcd = o3d.geometry.PointCloud()
    pcd.points = o3d.utility.Vector3dVector(points)

    pcd.estimate_normals(search_param=o3d.geometry.KDTreeSearchParamKNN(knn=k_neighbors))
    pcd.orient_normals_consistent_tangent_plane(k_neighbors)

    o3d.visualization.draw_geometries([pcd], point_show_normal=True)


def main():
    plot_perturbed_bubble(A=0.10, m=15, n=2, density=1000, slice_u=np.radians(30))
    plot_point_cloud_o3d(A=0.10, m=15, n=2, density=400, k_neighbors=30)

if __name__ == "__main__":
    main()
