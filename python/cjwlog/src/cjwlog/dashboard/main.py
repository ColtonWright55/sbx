import altair as alt
import pandas as pd
import streamlit as st

from cjwlog.dashboard.charts import events_in_window, plot_with_now
from cjwlog.dashboard.pharmacokinetics import CAFFEINE_MG, bac_curve, caffeine_curve, creatine_saturation_curve
from cjwlog.dashboard.sleep_debt import sleep_debt_curve
from cjwlog.dashboard.weight import weight_chart
from cjwlog.db import get_connection

alt.data_transformers.disable_max_rows()

st.set_page_config(page_title="Wellness Dashboard", layout="wide")
st.title("Wellness Dashboard")

conn = get_connection()
now = pd.Timestamp.now(tz="UTC")

st.header("Near-term")
NEAR_RANGES = {
    "Near-term (±12h)": (pd.Timedelta(hours=12), pd.Timedelta(hours=12)),
    "Past week": (pd.Timedelta(days=7), pd.Timedelta(0)),
    "Past 30 days": (pd.Timedelta(days=30), pd.Timedelta(0)),
}
near_label = st.radio("Range", list(NEAR_RANGES), horizontal=True, label_visibility="collapsed", key="near_range")
near_lookback, near_lookahead = NEAR_RANGES[near_label]
near_start, near_end = now - near_lookback, now + near_lookahead

st.subheader("Blood Alcohol Content (est.)")
plot_with_now(
    now,
    bac_curve(conn, near_start, near_end),
    "BAC %",
    "#2a78d6",
    events=events_in_window(conn, "alcohol", near_start, near_end),
)

st.subheader("Blood Caffeine Concentration (est.)")
plot_with_now(
    now,
    caffeine_curve(conn, near_start, near_end),
    "mg/L",
    "#6f4e37",
    events=events_in_window(conn, "coffee", near_start, near_end, size_col="name"),
    size_domain=(min(CAFFEINE_MG.values()), max(CAFFEINE_MG.values())),
)

st.header("Trends")
LONG_RANGES = {
    "Past week": pd.Timedelta(days=7),
    "Past 30 days": pd.Timedelta(days=30),
    "Past 90 days": pd.Timedelta(days=90),
}
long_label = st.radio("Long-range window", list(LONG_RANGES), horizontal=True, label_visibility="collapsed", key="long_range")
long_start = now - LONG_RANGES[long_label]

st.subheader("Weight")
weight_chart(conn, long_start, now)

st.subheader("Creatine Saturation (est., % of steady state)")
plot_with_now(
    now,
    creatine_saturation_curve(conn, long_start, now + pd.Timedelta(days=14)),
    "%",
    "#4a3aa7",
    events=events_in_window(conn, "supplement", long_start, now, name="Creatine"),
)

st.subheader("Sleep Debt (14-day rolling)")
plot_with_now(now, sleep_debt_curve(conn), "hrs", "#1baf7a")
