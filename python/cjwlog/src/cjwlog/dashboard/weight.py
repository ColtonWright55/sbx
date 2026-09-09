import altair as alt
import numpy as np
import pandas as pd
import streamlit as st

from cjwlog.dashboard.styles import AXIS, GRID, MUTED


def weight_series(conn) -> pd.DataFrame:
    df = pd.read_sql_query("SELECT logged_at, weight_lbs FROM weight ORDER BY logged_at", conn)
    if not df.empty:
        df["logged_at"] = pd.to_datetime(df["logged_at"], utc=True)
    return df


def weight_trend(df: pd.DataFrame, days: int = 7) -> tuple[pd.DataFrame, float] | None:
    if df.empty:
        return None
    cutoff = df["logged_at"].max() - pd.Timedelta(days=days)
    recent = df[df["logged_at"] >= cutoff]
    if len(recent) < 2:
        return None
    x_days = (recent["logged_at"] - recent["logged_at"].min()).dt.total_seconds() / 86400
    slope, intercept = np.polyfit(x_days, recent["weight_lbs"], 1)
    span = pd.Series([0, x_days.max()])
    line = pd.DataFrame(
        {"time": [recent["logged_at"].min(), recent["logged_at"].max()], "value": intercept + slope * span}
    )
    return line, slope


def weight_chart(conn, start: pd.Timestamp, end: pd.Timestamp) -> None:
    df = weight_series(conn)
    if df.empty:
        st.caption("No weight entries yet.")
        return
    df = df[(df["logged_at"] >= start) & (df["logged_at"] <= end)]
    if df.empty:
        st.caption("No weight entries in this range.")
        return

    points = alt.Chart(df).mark_circle(size=70, color="#2a78d6", opacity=0.85).encode(
        x=alt.X("logged_at:T", title=None, axis=alt.Axis(grid=False, domainColor=AXIS, tickColor=AXIS, labelColor=MUTED)),
        y=alt.Y(
            "weight_lbs:Q",
            title="lb",
            scale=alt.Scale(domain=[180, 225]),
            axis=alt.Axis(gridColor=GRID, domain=False, tickColor=AXIS, labelColor=MUTED, titleColor=MUTED),
        ),
    )
    layers = [points]
    result = weight_trend(df)
    if result is not None:
        trend_df, slope = result
        layers.append(alt.Chart(trend_df).mark_line(color=MUTED, strokeWidth=2).encode(x="time:T", y="value:Q"))
        label = pd.DataFrame(
            {
                "time": [trend_df["time"].iloc[-1]],
                "value": [trend_df["value"].iloc[-1]],
                "text": [f"{slope:+.2f} lb/day"],
            }
        )
        layers.append(
            alt.Chart(label)
            .mark_text(align="left", dx=8, dy=-6, color=MUTED, fontSize=12)
            .encode(x="time:T", y="value:Q", text="text:N")
        )

    chart = alt.layer(*layers).properties(height=220).configure_view(strokeWidth=0)
    st.altair_chart(chart, use_container_width=True)
