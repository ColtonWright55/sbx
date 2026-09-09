import re
from datetime import timedelta

import numpy as np
import pandas as pd

LBS_TO_KG = 0.45359237
DEFAULT_WEIGHT_KG = 90.0
STEP_MINUTES = 5

# Caffeine: one-compartment oral absorption/elimination model.
# mg per size pegged to Starbucks brewed (Pike Place) Tall/Grande/Venti, for an easy mental reference.
CAFFEINE_MG = {"Small": 235, "Medium": 310, "Large": 410}
CAFFEINE_HALFLIFE_HR = 5.0
CAFFEINE_KA_PER_HR = 6.0  # absorption rate -> Tmax ~40min
CAFFEINE_VD_L_PER_KG = 0.5

# Alcohol: Widmark zero-order model.
ALCOHOL_GRAMS_PER_DRINK = {"Beer": 14, "Wine": 14, "Liquor": 14}  # 1 US standard drink
WIDMARK_R_MALE = 0.68
ALCOHOL_ELIM_PCT_PER_HR = 0.017

FOOD_ABSORPTION_FACTOR = {"Meal": 0.80, "Snack": 0.92}
FOOD_WINDOW = timedelta(hours=2)

# Pinned to the aggressive (2%) end -- errs toward "take more," not toward complacency.
CREATINE_DAILY_DECAY_PCT = 0.02


def _parse_multiplier(amount: str | None) -> float:
    if not amount:
        return 1.0
    m = re.match(r"[\d.]+", amount.strip())
    return float(m.group()) if m else 1.0


def latest_weight_kg(conn) -> float:
    row = conn.execute("SELECT weight_lbs FROM weight ORDER BY logged_at DESC LIMIT 1").fetchone()
    return row["weight_lbs"] * LBS_TO_KG if row else DEFAULT_WEIGHT_KG


def load_intake(conn, category: str) -> pd.DataFrame:
    df = pd.read_sql_query(
        "SELECT logged_at, name, amount FROM intake WHERE category = ? ORDER BY logged_at",
        conn,
        params=(category,),
    )
    if not df.empty:
        df["logged_at"] = pd.to_datetime(df["logged_at"], utc=True)
    return df


def caffeine_curve(conn, start: pd.Timestamp, end: pd.Timestamp) -> pd.Series:
    doses = load_intake(conn, "coffee")
    grid = pd.date_range(start, end, freq=f"{STEP_MINUTES}min")
    level = np.zeros(len(grid))

    if not doses.empty:
        weight_kg = latest_weight_kg(conn)
        vd_l = CAFFEINE_VD_L_PER_KG * weight_kg
        ke = np.log(2) / CAFFEINE_HALFLIFE_HR
        ka = CAFFEINE_KA_PER_HR
        for _, dose in doses.iterrows():
            mg = CAFFEINE_MG.get(dose["name"], 100) * _parse_multiplier(dose["amount"])
            dt_hr = np.clip((grid - dose["logged_at"]).total_seconds() / 3600, 0, None)
            contrib = np.where(
                dt_hr > 0,
                (mg * ka) / (vd_l * (ka - ke)) * (np.exp(-ke * dt_hr) - np.exp(-ka * dt_hr)),
                0.0,
            )
            level += contrib

    return pd.Series(level, index=grid, name="caffeine_mg_per_l")


def bac_curve(conn, start: pd.Timestamp, end: pd.Timestamp) -> pd.Series:
    drinks = load_intake(conn, "alcohol")
    food = load_intake(conn, "food")
    grid = pd.date_range(start, end, freq=f"{STEP_MINUTES}min")
    dt_hours = STEP_MINUTES / 60

    weight_kg = latest_weight_kg(conn)
    pct_per_gram = 0.1 / (WIDMARK_R_MALE * weight_kg)

    events = []
    for _, d in drinks.iterrows():
        grams = ALCOHOL_GRAMS_PER_DRINK.get(d["name"], 14) * _parse_multiplier(d["amount"])
        nearby = food[
            (food["logged_at"] >= d["logged_at"] - FOOD_WINDOW)
            & (food["logged_at"] <= d["logged_at"] + FOOD_WINDOW)
        ]
        factor = min((FOOD_ABSORPTION_FACTOR.get(n, 1.0) for n in nearby["name"]), default=1.0)
        events.append((d["logged_at"], grams * factor * pct_per_gram))
    events.sort(key=lambda e: e[0])

    values = np.zeros(len(grid))
    level = 0.0
    ei = 0
    for i, t in enumerate(grid):
        while ei < len(events) and events[ei][0] <= t:
            level += events[ei][1]
            ei += 1
        level = max(0.0, level - ALCOHOL_ELIM_PCT_PER_HR * dt_hours)
        values[i] = level

    return pd.Series(values, index=grid, name="bac_pct")


def creatine_saturation_curve(conn, start: pd.Timestamp, end: pd.Timestamp) -> pd.Series:
    """% of steady-state muscle saturation under a one-dose-per-day accumulation model."""
    doses = load_intake(conn, "supplement")
    doses = doses[doses["name"] == "Creatine"] if not doses.empty else doses
    dose_days = set(doses["logged_at"].dt.date) if not doses.empty else set()

    retention = 1 - CREATINE_DAILY_DECAY_PCT
    steady_state = 1 / CREATINE_DAILY_DECAY_PCT

    grid = pd.date_range(start.normalize(), end.normalize(), freq="1D", tz=start.tz)
    values = np.zeros(len(grid))
    level = 0.0
    for i, day in enumerate(grid):
        level *= retention
        if day.date() in dose_days:
            level += 1.0
        values[i] = level

    return pd.Series(values / steady_state * 100, index=grid, name="creatine_saturation_pct")
