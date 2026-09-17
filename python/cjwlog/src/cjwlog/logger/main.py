import json
import os
import secrets
from datetime import datetime, timedelta, timezone
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

WORK_CATEGORIES = ["Coding", "Lab Work", "Writing", "Study/Learning", "Fundamental Research"]

WORK_TAGS = ["Volunteer"]

WORK_STOP = "Stopped"


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
            SELECT 'weight' AS table_name, id, logged_at, 'Weight ' || weight_lbs || ' lbs' AS description FROM weight
            UNION ALL
            SELECT 'intake', id, logged_at, category || ': ' || name || COALESCE(' (' || amount || ')', '') FROM intake
            UNION ALL
            SELECT 'psychiatric', id, logged_at, 'Mood ' || mood FROM psychiatric WHERE mood IS NOT NULL
            UNION ALL
            SELECT 'psychiatric', id, logged_at, 'Energy ' || energy FROM psychiatric WHERE energy IS NOT NULL
            UNION ALL
            SELECT 'note', id, logged_at, text FROM note
            ORDER BY logged_at DESC
            LIMIT 15
            """
        ).fetchall()
    cutoff = undo_cutoff()
    recent = [
        dict(row, can_undo=row["logged_at"] > cutoff, display_time=to_display(row["logged_at"]))
        for row in rows
    ]
    return templates.TemplateResponse(
        request,
        "index.html",
        {
            "recent": recent,
            "food": FOOD,
            "exercise": EXERCISE,
            "substances": SUBSTANCES,
            "now_local": datetime.now().strftime("%Y-%m-%dT%H:%M"),
        },
    )


@app.get("/work")
def work_page(request: Request):
    with get_connection() as conn:
        current = conn.execute(
            "SELECT category, tag, logged_at FROM work_log ORDER BY logged_at DESC LIMIT 1"
        ).fetchone()
        rows = conn.execute(
            """
            SELECT 'work_log' AS table_name, id, logged_at, category || COALESCE(' (' || tag || ')', '') AS description FROM work_log
            UNION ALL
            SELECT 'note', id, logged_at, text FROM note
            ORDER BY logged_at DESC
            LIMIT 15
            """
        ).fetchall()
    cutoff = undo_cutoff()
    recent = [
        dict(row, can_undo=row["logged_at"] > cutoff, display_time=to_display(row["logged_at"]))
        for row in rows
    ]
    return templates.TemplateResponse(
        request,
        "work.html",
        {
            "categories": WORK_CATEGORIES,
            "tags": WORK_TAGS,
            "stop": WORK_STOP,
            "current": dict(current) if current else None,
            "recent": recent,
        },
    )


@app.post("/work")
def log_work(category: str = Form(...), tag: str = Form("")):
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO work_log (logged_at, category, tag) VALUES (?, ?, ?)", (now(), category, tag or None)
        )
    sync_to_remote()
    return RedirectResponse("/work", status_code=303)


@app.post("/weight")
def log_weight(weight_lbs: float = Form(...)):
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO weight (logged_at, weight_lbs) VALUES (?, ?)", (now(), weight_lbs)
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
def log_note(text: str = Form(...), back: str = Form("/")):
    with get_connection() as conn:
        conn.execute("INSERT INTO note (logged_at, text) VALUES (?, ?)", (now(), text))
    sync_to_remote()
    return RedirectResponse(back, status_code=303)


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


@app.get("/map")
def map_page(request: Request):
    return templates.TemplateResponse(request, "map.html", {})


@app.get("/gps.json")
def gps_json(days: int = 3):
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT latitude, longitude, logged_at FROM gps WHERE logged_at > ? ORDER BY logged_at",
            (cutoff,),
        ).fetchall()
    return [dict(row) for row in rows]


HEALTH_KNOWN_KEYS = {"date", "qty", "start", "end", "source"}
HEALTH_SAMPLE_DIR = Path("data/health_samples")


def parse_health_date(s: str) -> str:
    return datetime.strptime(s, "%Y-%m-%d %H:%M:%S %z").astimezone(timezone.utc).isoformat()


@app.post("/health")
async def health(request: Request):
    body = await request.body()
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    HEALTH_SAMPLE_DIR.mkdir(parents=True, exist_ok=True)
    (HEALTH_SAMPLE_DIR / f"{ts}.json").write_bytes(body)

    payload = json.loads(body)
    metrics = payload.get("data", {}).get("metrics", [])
    dropped = 0
    with get_connection() as conn:
        for metric in metrics:
            name = metric.get("name")
            units = metric.get("units")
            for row in metric.get("data", []):
                extra = {k: v for k, v in row.items() if k not in HEALTH_KNOWN_KEYS}
                try:
                    conn.execute(
                        """
                        INSERT INTO health_metric
                            (logged_at, metric, units, source, start_at, end_at, qty, extra)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            parse_health_date(row["date"]),
                            name,
                            units,
                            row.get("source"),
                            parse_health_date(row["start"]) if "start" in row else None,
                            parse_health_date(row["end"]) if "end" in row else None,
                            row.get("qty"),
                            json.dumps(extra) if extra else None,
                        ),
                    )
                except Exception as e:
                    dropped += 1
                    print(f"[cjwlog] health row dropped (metric={name}): {e}")
    if dropped:
        print(f"[cjwlog] health sample {ts}.json: {dropped} row(s) dropped, raw json kept for replay")
    sync_to_remote()
    return {}


UNDOABLE_TABLES = {"weight", "intake", "psychiatric", "note", "work_log"}


@app.post("/undo")
def undo(table: str = Form(...), id: int = Form(...), back: str = Form("/")):
    if table not in UNDOABLE_TABLES:
        return RedirectResponse(back, status_code=303)
    with get_connection() as conn:
        conn.execute(f"DELETE FROM {table} WHERE id = ? AND logged_at > ?", (id, undo_cutoff()))
    sync_to_remote()
    return RedirectResponse(back, status_code=303)
