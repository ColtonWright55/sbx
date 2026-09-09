import pandas as pd

TARGET_SLEEP_HOURS = 8.0
SLEEP_DEBT_WINDOW_DAYS = 14


def sleep_debt_curve(conn) -> pd.Series:
    df = pd.read_sql_query("SELECT bedtime, wake_time FROM sleep ORDER BY bedtime", conn)
    if df.empty:
        return pd.Series(dtype=float)

    bedtime = pd.to_datetime(df["bedtime"], utc=True)
    wake_time = pd.to_datetime(df["wake_time"], utc=True)
    hours_slept = (wake_time - bedtime).dt.total_seconds() / 3600

    deficit = pd.Series((TARGET_SLEEP_HOURS - hours_slept).values, index=bedtime)
    debt = deficit.rolling(f"{SLEEP_DEBT_WINDOW_DAYS}D").sum().clip(lower=0)
    debt.name = "sleep_debt_hours"
    return debt
