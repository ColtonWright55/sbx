import numpy as np
import matplotlib.pyplot as plt
import pyvista as pv

def generate_random_matrices():
    """Generates random 2x2 PD and PSD matrices using eigendecomposition."""
    theta_pd = np.random.uniform(0, 2 * np.pi)
    theta_psd = np.random.uniform(0, 2 * np.pi)

    # Rotation matrices
    R_pd = np.array([[np.cos(theta_pd), -np.sin(theta_pd)],
                     [np.sin(theta_pd),  np.cos(theta_pd)]])
    R_psd = np.array([[np.cos(theta_psd), -np.sin(theta_psd)],
                      [np.sin(theta_psd),  np.cos(theta_psd)]])

    # PD: strictly positive, scaled to look good on a plot
    eig_pd = [np.random.uniform(0.5, 2.5), np.random.uniform(0.5, 2.5)]
    # PSD: one strictly zero to guarantee the flat valley, one positive
    eig_psd = [np.random.uniform(1.0, 3.0), 0.0]

    # Construct matrices: A = R * Lambda * R^T
    A_pd = R_pd @ np.diag(eig_pd) @ R_pd.T
    A_psd = R_psd @ np.diag(eig_psd) @ R_psd.T

    return A_pd, A_psd, eig_pd, eig_psd

def main():
    x = np.linspace(-2, 2, 30)
    y = np.linspace(-2, 2, 30)
    X, Y = np.meshgrid(x, y)

    A_pd, A_psd, eig_pd, eig_psd = generate_random_matrices()
    pts = np.stack([X, Y], axis=-1)  # shape (30, 30, 2)

    # Quadratic form: Z = x^T A x = <x, Ax>, evaluated at every grid point
    Z_pd = np.einsum('...i,ij,...j->...', pts, A_pd, pts)
    Z_psd = np.einsum('...i,ij,...j->...', pts, A_psd, pts)

    # Vector field: (U, V) = A x
    UV_pd = np.einsum('ij,...j->...i', A_pd, pts)
    U_pd, V_pd = UV_pd[..., 0], UV_pd[..., 1]

    UV_psd = np.einsum('ij,...j->...i', A_psd, pts)
    U_psd, V_psd = UV_psd[..., 0], UV_psd[..., 1]

    print(f"PD Matrix:\n{A_pd}\nEigenvalues: {eig_pd}")
    print(f"PSD Matrix:\n{A_psd}\nEigenvalues: {eig_psd}")

    skip = (slice(None, None, 3), slice(None, None, 3))

    grid_pd = pv.StructuredGrid(X, Y, Z_pd)
    plotter_pd = pv.Plotter()
    plotter_pd.set_background("white")
    plotter_pd.add_mesh(grid_pd, scalars=Z_pd.ravel(order="F"), cmap="viridis", show_scalar_bar=False)
    plotter_pd.show_grid(xtitle="x", ytitle="y", ztitle="energy", color="black")
    plotter_pd.add_axes()
    plotter_pd.add_title(f"PD Energy Landscape (Bowl)  eigenvalues: {eig_pd[0]:.2f}, {eig_pd[1]:.2f}", font_size=10, color="black")
    plotter_pd.show()

    grid_psd = pv.StructuredGrid(X, Y, Z_psd)
    plotter_psd = pv.Plotter()
    plotter_psd.set_background("white")
    plotter_psd.add_mesh(grid_psd, scalars=Z_psd.ravel(order="F"), cmap="plasma", show_scalar_bar=False)
    plotter_psd.show_grid(xtitle="x", ytitle="y", ztitle="energy", color="black")
    plotter_psd.add_axes()
    plotter_psd.add_title(f"PSD Energy Landscape (Trough)  eigenvalues: {eig_psd[0]:.2f}, {eig_psd[1]:.2f}", font_size=10, color="black")
    plotter_psd.show()

    fig3, ax3 = plt.subplots()
    cs3 = ax3.contourf(X, Y, Z_pd, cmap="viridis", alpha=0.5)
    ax3.quiver(X[skip], Y[skip], U_pd[skip], V_pd[skip], color="black")
    ax3.plot(0, 0, "ko", ms=10)
    ax3.set_title("PD Vector Field & Level Sets\n(Ellipses with Unique Minimum)")
    ax3.set_xlabel("x")
    ax3.set_ylabel("y")
    ax3.grid(True, alpha=0.3)
    ax3.set_aspect("equal")
    fig3.colorbar(cs3, ax=ax3, label="energy")

    fig4, ax4 = plt.subplots()
    cs4 = ax4.contourf(X, Y, Z_psd, cmap="plasma", alpha=0.5)
    ax4.quiver(X[skip], Y[skip], U_psd[skip], V_psd[skip], color="black")
    ax4.plot(0, 0, "ko", ms=10)
    ax4.set_title("PSD Vector Field & Level Sets\n(Parallel Lines with Infinite Minima)")
    ax4.set_xlabel("x")
    ax4.set_ylabel("y")
    ax4.grid(True, alpha=0.3)
    ax4.set_aspect("equal")
    fig4.colorbar(cs4, ax=ax4, label="energy")

    plt.show()

if __name__ == "__main__":
    main()
