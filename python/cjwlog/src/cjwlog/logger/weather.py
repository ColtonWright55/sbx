import json
import urllib.parse
import urllib.request
from datetime import datetime

# Columbus, OH -- placeholder default until location is derived from GPS at the time of the run.
DEFAULT_LAT = 39.9612
DEFAULT_LON = -82.9988


def fetch_weather(dt: datetime, lat: float = DEFAULT_LAT, lon: float = DEFAULT_LON) -> tuple[float, float, float] | None:
    """(temp_f, humidity_pct, solar_radiation_wm2) for the UTC hour nearest dt, or None on any failure."""
    params = {
        "latitude": lat,
        "longitude": lon,
        "hourly": "temperature_2m,relative_humidity_2m,shortwave_radiation",
        "temperature_unit": "fahrenheit",
        "timezone": "UTC",
        "past_days": 2,
        "forecast_days": 1,
    }
    url = "https://api.open-meteo.com/v1/forecast?" + urllib.parse.urlencode(params)
    try:
        with urllib.request.urlopen(url, timeout=5) as resp:
            data = json.load(resp)
        times = data["hourly"]["time"]
        idx = times.index(dt.strftime("%Y-%m-%dT%H:00"))
        hourly = data["hourly"]
        return hourly["temperature_2m"][idx], hourly["relative_humidity_2m"][idx], hourly["shortwave_radiation"][idx]
    except Exception as e:
        print(f"[cjwlog] weather fetch failed: {e}")
        return None
