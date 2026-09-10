import os
import shutil
import sqlite3
from pathlib import Path

import tbxdata  # loads ~/.config/tbxdata/.env and exposes LOCAL_MOUNT

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DB_PATH = Path(os.environ.get("CJWLOG_DB_PATH", PROJECT_ROOT / "data" / "cjwlog.db"))

# This app runs on the same box that hosts SeaweedFS, so the bucket is just a local
# FUSE-mounted directory (tbxdata's "local passthrough") -- plain file copy, no S3/network.
BUCKET_PATH = Path(os.environ.get(
    "CJWLOG_BUCKET_PATH",
    Path(tbxdata.LOCAL_MOUNT) / "buckets" / os.environ["SEAWEED_BUCKET_NAME"] / "cjwlog" / "cjwlog.db",
))

SCHEMA = """
CREATE TABLE IF NOT EXISTS sleep (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    logged_at TEXT NOT NULL,
    bedtime TEXT NOT NULL,
    wake_time TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS weight (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    logged_at TEXT NOT NULL,
    weight_lbs REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS intake (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    logged_at TEXT NOT NULL,
    category TEXT NOT NULL,
    name TEXT NOT NULL,
    amount TEXT
);

CREATE TABLE IF NOT EXISTS psychiatric (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    logged_at TEXT NOT NULL,
    mood INTEGER,
    energy INTEGER
);

CREATE TABLE IF NOT EXISTS note (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    logged_at TEXT NOT NULL,
    text TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS gps (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    logged_at TEXT NOT NULL,
    latitude REAL NOT NULL,
    longitude REAL NOT NULL,
    accuracy_m REAL,
    altitude_m REAL,
    velocity_kmh REAL,
    battery_pct INTEGER,
    tid TEXT
);

CREATE TABLE IF NOT EXISTS health_metric (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    logged_at TEXT NOT NULL,
    metric TEXT NOT NULL,
    units TEXT,
    source TEXT,
    start_at TEXT,
    end_at TEXT,
    qty REAL,
    extra TEXT
);

CREATE INDEX IF NOT EXISTS idx_health_metric_lookup ON health_metric(metric, logged_at);
"""


def get_connection() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _ensure_column(conn: sqlite3.Connection, table: str, column: str, coltype: str) -> None:
    existing = {row[1] for row in conn.execute(f"PRAGMA table_info({table})")}
    if column not in existing:
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {coltype}")


def init_db() -> None:
    restore_from_remote_if_missing()
    with get_connection() as conn:
        conn.executescript(SCHEMA)
        _ensure_column(conn, "intake", "temp_f", "REAL")
        _ensure_column(conn, "intake", "humidity_pct", "REAL")
        _ensure_column(conn, "intake", "solar_radiation", "REAL")


def restore_from_remote_if_missing() -> None:
    """Seed DB_PATH from the SeaweedFS backup if this machine has no local copy yet."""
    if DB_PATH.exists() or not BUCKET_PATH.exists():
        return
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(BUCKET_PATH, DB_PATH)


def sync_to_remote() -> None:
    """Copy the current DB file into the SeaweedFS bucket so it lives alongside your other data."""
    try:
        BUCKET_PATH.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(DB_PATH, BUCKET_PATH)
    except Exception as e:
        print(f"[cjwlog] failed to sync db to tbxdata: {e}")
