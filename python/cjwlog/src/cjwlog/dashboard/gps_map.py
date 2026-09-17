import json

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

MAX_POINTS = 5000


def gps_map(conn, start: pd.Timestamp, end: pd.Timestamp, height: int = 500) -> None:
    df = pd.read_sql_query("SELECT latitude, longitude, logged_at FROM gps ORDER BY logged_at", conn)
    if df.empty:
        st.caption("No GPS points yet.")
        return
    df["logged_at"] = pd.to_datetime(df["logged_at"], utc=True, format="ISO8601")
    df = df[(df["logged_at"] >= start) & (df["logged_at"] <= end)]
    if df.empty:
        st.caption("No GPS points in this range.")
        return
    if len(df) > MAX_POINTS:
        df = df.iloc[:: len(df) // MAX_POINTS]

    points = df[["latitude", "longitude"]].to_dict("records")
    components.html(_MAP_HTML.replace("__POINTS__", json.dumps(points)), height=height)


_MAP_HTML = """
<div id="map" style="height: 100%; background: #111;"></div>
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css">
<style>.leaflet-tile-pane { filter: invert(1) hue-rotate(180deg) brightness(0.95) contrast(0.9); }</style>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script>
  const points = __POINTS__;
  const map = L.map('map', { zoomControl: false, attributionControl: false });
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    subdomains: 'abc', maxZoom: 19,
  }).addTo(map);

  const latlngs = points.map(p => [p.latitude, p.longitude]);
  L.polyline(latlngs, { color: '#4da6ff', weight: 2, opacity: 0.6 }).addTo(map);

  points.forEach((p, i) => {
    const age = points.length > 1 ? i / (points.length - 1) : 1;
    L.circleMarker([p.latitude, p.longitude], {
      radius: 3 + age * 3, color: '#ff5c33', fillColor: '#ff5c33',
      fillOpacity: 0.3 + age * 0.6, stroke: false,
    }).addTo(map);
  });
  map.fitBounds(latlngs, { padding: [20, 20] });
</script>
"""
