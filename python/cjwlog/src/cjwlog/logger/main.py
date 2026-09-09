import os
import secrets
from datetime import datetime, time, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

from fastapi import BackgroundTasks, Depends, FastAPI, Form, HTTPException
from fastapi.responses import RedirectResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.templating import Jinja2Templates
from starlette.requests import Request

from cjwlog.db import get_connection, init_db, sync_to_remote
from cjwlog.logger.weather import fetch_weather

app = FastAPI()
templates = Jinja2Templates(directory=Path(__file__).parent / "templates")

FOOD = ["Snack", "Meal"]

EXERCISE = ["Run", "Weights"]

SUBSTANCES = [
    ("coffee", "Coffee", ["Small", "Medium", "Large"]),
    ("alcohol", "Alcohol", ["Beer", "Wine", "Liquor"]),
    ("supplement", "Supplements", ["Creatine", "Multivitamin", "Melatonin"]),
]


UNDO_WINDOW = timedelta(hours=2)

OWNTRACKS_USER = os.environ.get("CJWLOG_OWNTRACKS_USER")
OWNTRACKS_PASS = os.environ.get("CJWLOG_OWNTRACKS_PASS")
owntracks_security = HTTPBasic(auto_error=False)


def check_owntracks_auth(credentials: HTTPBasicCredentials | None = Depends(owntracks_security)) -> None:
    if not OWNTRACKS_USER:
        return
    valid = (
        credentials is not None
        and secrets.compare_digest(credentials.username, OWNTRACKS_USER)
        and secrets.compare_digest(credentials.password, OWNTRACKS_PASS)
    )
    if not valid:
        raise HTTPException(status_code=401, detail="Unauthorized", headers={"WWW-Authenticate": "Basic"})


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def to_utc_iso(local_str: str) -> str:
    return datetime.strptime(local_str, "%Y-%m-%dT%H:%M").astimezone(timezone.utc).isoformat()


DISPLAY_TZ = ZoneInfo("America/New_York")


def to_display(utc_iso: str) -> str:
    return datetime.fromisoformat(utc_iso).astimezone(DISPLAY_TZ).strftime("%Y-%m-%d %H:%M")


def undo_cutoff() -> str:
    return (datetime.now(timezone.utc) - UNDO_WINDOW).isoformat()


@app.on_event("startup")
def startup() -> None:
    init_db()


@app.get("/")
def index(request: Request):
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT 'weight' AS table_name, id, logged_at, 'Weight ' || weight_lbs || ' lbs' AS description, NULL AS bedtime, NULL AS wake_time FROM weight
            UNION ALL
            SELECT 'sleep', id, logged_at, NULL, bedtime, wake_time FROM sleep
            UNION ALL
            SELECT 'intake', id, logged_at, category || ': ' || name || COALESCE(' (' || amount || ')', ''), NULL, NULL FROM intake
            UNION ALL
            SELECT 'psychiatric', id, logged_at, 'Mood ' || mood, NULL, NULL FROM psychiatric WHERE mood IS NOT NULL
            UNION ALL
            SELECT 'psychiatric', id, logged_at, 'Energy ' || energy, NULL, NULL FROM psychiatric WHERE energy IS NOT NULL
            UNION ALL
            SELECT 'note', id, logged_at, text, NULL, NULL FROM note
            ORDER BY logged_at DESC
            LIMIT 15
            """
        ).fetchall()
    cutoff = undo_cutoff()
    recent = []
    for row in rows:
        entry = dict(row, can_undo=row["logged_at"] > cutoff, display_time=to_display(row["logged_at"]))
        if entry["table_name"] == "sleep":
            entry["description"] = f"Sleep {to_display(row['bedtime'])} -> {to_display(row['wake_time'])}"
        recent.append(entry)
    today = datetime.now().date()
    default_bedtime = datetime.combine(today - timedelta(days=1), time(23, 5))
    default_wake = datetime.combine(today, time(8, 0))
    return templates.TemplateResponse(
        request,
        "index.html",
        {
            "recent": recent,
            "food": FOOD,
            "exercise": EXERCISE,
            "substances": SUBSTANCES,
            "scale": range(1, 11),
            "default_bedtime": default_bedtime.strftime("%Y-%m-%dT%H:%M"),
            "default_wake": default_wake.strftime("%Y-%m-%dT%H:%M"),
            "now_local": datetime.now().strftime("%Y-%m-%dT%H:%M"),
        },
    )


@app.post("/weight")
def log_weight(weight_lbs: float = Form(...)):
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO weight (logged_at, weight_lbs) VALUES (?, ?)", (now(), weight_lbs)
        )
    sync_to_remote()
    return RedirectResponse("/", status_code=303)


@app.post("/sleep")
def log_sleep(bedtime: str = Form(...), wake_time: str = Form(...)):
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO sleep (logged_at, bedtime, wake_time) VALUES (?, ?, ?)",
            (now(), to_utc_iso(bedtime), to_utc_iso(wake_time)),
        )
    sync_to_remote()
    return RedirectResponse("/", status_code=303)


def _attach_weather(row_id: int, logged_at_iso: str) -> None:
    weather = fetch_weather(datetime.fromisoformat(logged_at_iso))
    if weather is None:
        return
    temp_f, humidity_pct, solar_radiation = weather
    with get_connection() as conn:
        conn.execute(
            "UPDATE intake SET temp_f = ?, humidity_pct = ?, solar_radiation = ? WHERE id = ?",
            (temp_f, humidity_pct, solar_radiation, row_id),
        )
    sync_to_remote()


@app.post("/intake")
def log_intake(
    background_tasks: BackgroundTasks,
    category: str = Form(""),
    name: str = Form(""),
    combo: str = Form(""),
    amount: str = Form(""),
    logged_at: str = Form(""),
):
    if combo:
        category, name = combo.split("|", 1)
    logged_at_iso = to_utc_iso(logged_at) if logged_at else now()
    with get_connection() as conn:
        cur = conn.execute(
            "INSERT INTO intake (logged_at, category, name, amount) VALUES (?, ?, ?, ?)",
            (logged_at_iso, category, name, amount or None),
        )
    if category == "exercise" and name == "Run":
        background_tasks.add_task(_attach_weather, cur.lastrowid, logged_at_iso)
    sync_to_remote()
    return RedirectResponse("/", status_code=303)


@app.post("/psychiatric")
def log_psychiatric(mood: str = Form(""), energy: str = Form("")):
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO psychiatric (logged_at, mood, energy) VALUES (?, ?, ?)",
            (now(), mood or None, energy or None),
        )
    sync_to_remote()
    return RedirectResponse("/", status_code=303)


@app.post("/note")
def log_note(text: str = Form(...)):
    with get_connection() as conn:
        conn.execute("INSERT INTO note (logged_at, text) VALUES (?, ?)", (now(), text))
    sync_to_remote()
    return RedirectResponse("/", status_code=303)


@app.post("/owntracks")
async def owntracks(request: Request, _auth: None = Depends(check_owntracks_auth)):
    payload = await request.json()
    items = payload if isinstance(payload, list) else [payload]
    with get_connection() as conn:
        for item in items:
            if item.get("_type") != "location":
                continue
            conn.execute(
                """
                INSERT INTO gps
                    (logged_at, latitude, longitude, accuracy_m, altitude_m, velocity_kmh, battery_pct, tid)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    datetime.fromtimestamp(item["tst"], tz=timezone.utc).isoformat(),
                    item["lat"],
                    item["lon"],
                    item.get("acc"),
                    item.get("alt"),
                    item.get("vel"),
                    item.get("batt"),
                    item.get("tid"),
                ),
            )
    sync_to_remote()
    return {}


UNDOABLE_TABLES = {"weight", "sleep", "intake", "psychiatric", "note"}


@app.post("/undo")
def undo(table: str = Form(...), id: int = Form(...)):
    if table not in UNDOABLE_TABLES:
        return RedirectResponse("/", status_code=303)
    with get_connection() as conn:
        conn.execute(f"DELETE FROM {table} WHERE id = ? AND logged_at > ?", (id, undo_cutoff()))
    sync_to_remote()
    return RedirectResponse("/", status_code=303)
