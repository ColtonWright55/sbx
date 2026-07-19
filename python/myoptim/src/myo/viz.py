import numpy as np


def build_grid(func, resolution=200):
    lower, upper = func.suggested_bounds()
    x = np.linspace(lower[0], upper[0], resolution)
    y = np.linspace(lower[1], upper[1], resolution)
    X, Y = np.meshgrid(x, y)
    Z = np.array([[func([xi, yi]) for xi in x] for yi in y])
    return X, Y, Z


def _title(func, result):
    base = type(func).__name__
    return base if result is None else f"{base} - {result.name}"


def plot_plotly(func, result=None, resolution=200):
    import plotly.graph_objects as go

    X, Y, Z = build_grid(func, resolution)
    data = [go.Surface(x=X, y=Y, z=Z, colorscale="Viridis", opacity=0.85)]

    if result is not None:
        traj = result.trajectory[result.n_init :]
        vals = result.values[result.n_init :]

        data.append(
            go.Scatter3d(
                x=traj[:, 0],
                y=traj[:, 1],
                z=vals,
                mode="lines",
                line=dict(color="gray", width=2),
                opacity=0.4,
                showlegend=False,
            )
        )
        data.append(
            go.Scatter3d(
                x=traj[:, 0],
                y=traj[:, 1],
                z=vals,
                mode="markers",
                marker=dict(size=3, color=np.arange(len(vals)), colorscale="Reds"),
                name=result.name,
            )
        )
        data.append(
            go.Scatter3d(
                x=[traj[0, 0], traj[-1, 0]],
                y=[traj[0, 1], traj[-1, 1]],
                z=[vals[0], vals[-1]],
                mode="markers+text",
                marker=dict(size=6, color=["blue", "green"]),
                text=["start", "end"],
                textposition="top center",
                showlegend=False,
            )
        )

    fig = go.Figure(data=data)
    fig.update_layout(
        title=_title(func, result),
        scene=dict(xaxis_title="x", yaxis_title="y", zaxis_title="f(x, y)"),
    )
    fig.show()


def plot_pyvista(func, result=None, resolution=200):
    import pyvista as pv

    X, Y, Z = build_grid(func, resolution)
    grid = pv.StructuredGrid(X, Y, Z)
    grid["height"] = Z.ravel(order="F")

    plotter = pv.Plotter()
    plotter.add_mesh(grid, scalars="height", cmap="viridis", smooth_shading=True, opacity=0.85)

    if result is not None:
        traj = result.trajectory[result.n_init :]
        vals = result.values[result.n_init :]
        points = np.column_stack([traj[:, 0], traj[:, 1], vals])

        plotter.add_lines(points, color="lightgray", width=1, connected=True)
        plotter.add_points(points, color="red", point_size=8, render_points_as_spheres=True)
        plotter.add_point_labels(
            points[[0]],
            ["start"],
            point_color="blue",
            point_size=14,
            font_size=20,
            render_points_as_spheres=True,
        )
        plotter.add_point_labels(
            points[[-1]],
            ["end"],
            point_color="green",
            point_size=14,
            font_size=20,
            render_points_as_spheres=True,
        )

    plotter.show_bounds(
        grid="back",
        location="outer",
        ticks="outside",
        xtitle="x",
        ytitle="y",
        ztitle="f(x, y)",
        color="black",
    )
    plotter.add_title(_title(func, result))
    plotter.show()
