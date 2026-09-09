import altair as alt
import pandas as pd
import streamlit as st

from cjwlog.dashboard.pharmacokinetics import CAFFEINE_MG, load_intake
from cjwlog.dashboard.styles import AXIS, GRID, MUTED


def events_in_window(
    conn, category: str, start: pd.Timestamp, end: pd.Timestamp, size_col: str | None = None, name: str | None = None
) -> pd.DataFrame:
    df = load_intake(conn, category)
    if df.empty:
        return pd.DataFrame(columns=["time", "size", "value"])
    if name is not None:
        df = df[df["name"] == name]
    df = df[(df["logged_at"] >= start) & (df["logged_at"] <= end)]
    size = df[size_col].map(CAFFEINE_MG).fillna(90) if size_col else 90
    return pd.DataFrame({"time": df["logged_at"], "size": size, "value": 0.0})


def plot_with_now(
    now: pd.Timestamp,
    series: pd.Series,
    y_title: str,
    color: str,
    events: pd.DataFrame | None = None,
    size_domain: tuple[float, float] | None = None,
) -> None:
    df = series.reset_index()
    df.columns = ["time", "value"]

    base = alt.Chart(df).encode(
        x=alt.X("time:T", title=None, axis=alt.Axis(grid=False, domainColor=AXIS, tickColor=AXIS, labelColor=MUTED)),
        y=alt.Y(
            "value:Q",
            title=y_title,
            axis=alt.Axis(gridColor=GRID, domain=False, tickColor=AXIS, labelColor=MUTED, titleColor=MUTED),
        ),
    )
    layers = [
        base.mark_area(opacity=0.1, color=color, line=False),
        base.mark_line(strokeWidth=2, color=color, strokeCap="round", strokeJoin="round"),
        alt.Chart(pd.DataFrame({"time": [now]}))
        .mark_rule(strokeDash=[3, 3], color=MUTED, strokeWidth=1)
        .encode(x="time:T"),
    ]
    if events is not None and not events.empty:
        scale_kwargs = {"range": [40, 260]}
        if size_domain is not None:
            scale_kwargs.update(domain=list(size_domain), zero=False)
        layers.append(
            alt.Chart(events)
            .mark_circle(color=color, opacity=0.85)
            .encode(
                x="time:T",
                y=alt.Y("value:Q", title=None),
                size=alt.Size("size:Q", legend=None, scale=alt.Scale(**scale_kwargs)),
            )
        )
    chart = alt.layer(*layers).properties(height=220).configure_view(strokeWidth=0)
    st.altair_chart(chart, use_container_width=True)
