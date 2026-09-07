import pandas as pd
import streamlit as st

from cjwlog.db import get_connection

st.set_page_config(page_title="Wellness Dashboard")
st.title("Wellness Dashboard")

conn = get_connection()

weight = pd.read_sql_query("SELECT logged_at, weight_lbs FROM weight ORDER BY logged_at", conn)
if not weight.empty:
    weight["logged_at"] = pd.to_datetime(weight["logged_at"])
    st.subheader("Weight")
    st.line_chart(weight.set_index("logged_at")["weight_lbs"])

sleep = pd.read_sql_query("SELECT bedtime, wake_time FROM sleep ORDER BY bedtime", conn)
if not sleep.empty:
    sleep["bedtime"] = pd.to_datetime(sleep["bedtime"])
    sleep["wake_time"] = pd.to_datetime(sleep["wake_time"])
    sleep["hours"] = (sleep["wake_time"] - sleep["bedtime"]).dt.total_seconds() / 3600
    st.subheader("Sleep (hours)")
    st.line_chart(sleep.set_index("bedtime")["hours"])

psych = pd.read_sql_query("SELECT logged_at, mood, energy FROM psychiatric ORDER BY logged_at", conn)
if not psych.empty:
    psych["logged_at"] = pd.to_datetime(psych["logged_at"])
    mood = psych.dropna(subset=["mood"]).set_index("logged_at")["mood"]
    if not mood.empty:
        st.subheader("Mood")
        st.line_chart(mood)
    energy = psych.dropna(subset=["energy"]).set_index("logged_at")["energy"]
    if not energy.empty:
        st.subheader("Energy")
        st.line_chart(energy)

intake = pd.read_sql_query("SELECT category, name FROM intake", conn)
if not intake.empty:
    st.subheader("Substances")
    intake["label"] = intake["category"] + ": " + intake["name"]
    st.bar_chart(intake["label"].value_counts())
