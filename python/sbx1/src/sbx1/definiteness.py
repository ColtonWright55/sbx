import numpy as np
import plotly.graph_objects as go
import plotly.figure_factory as ff

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
    fig1 = go.Figure(data=go.Surface(x=X, y=Y, z=Z_pd, colorscale='Viridis'))
    fig1.update_layout(
        title=f"PD Energy Landscape (Bowl)<br>Eigenvalues: {eig_pd[0]:.2f}, {eig_pd[1]:.2f}",
        scene=dict(zaxis=dict(range=[-1, np.max(Z_pd) + 1])),
    )
    fig1.show()
    fig2 = go.Figure(data=go.Surface(x=X, y=Y, z=Z_psd, colorscale='Plasma'))
    fig2.update_layout(
        title=f"PSD Energy Landscape (Trough)<br>Eigenvalues: {eig_psd[0]:.2f}, {eig_psd[1]:.2f}",
        scene=dict(zaxis=dict(range=[-1, np.max(Z_pd) + 1])),
    )
    fig2.show()
    fig3 = ff.create_quiver(X[skip], Y[skip], U_pd[skip], V_pd[skip], scale=0.1, line=dict(color='black'))
    fig3.add_trace(go.Contour(x=x, y=y, z=Z_pd, colorscale='Viridis', opacity=0.5, showscale=False))
    fig3.add_trace(go.Scatter(x=[0], y=[0], mode='markers', marker=dict(color='black', size=10)))
    fig3.update_layout(title="PD Vector Field & Level Sets<br>(Ellipses with Unique Minimum)")
    fig3.update_yaxes(scaleanchor="x", scaleratio=1)
    fig3.show()
    fig4 = ff.create_quiver(X[skip], Y[skip], U_psd[skip], V_psd[skip], scale=0.1, line=dict(color='black'))
    fig4.add_trace(go.Contour(x=x, y=y, z=Z_psd, colorscale='Plasma', opacity=0.5, showscale=False))
    fig4.add_trace(go.Scatter(x=[0], y=[0], mode='markers', marker=dict(color='black', size=10)))
    fig4.update_layout(title="PSD Vector Field & Level Sets<br>(Parallel Lines with Infinite Minima)")
    fig4.update_yaxes(scaleanchor="x", scaleratio=1)
    fig4.show()

if __name__ == "__main__":
    main()
