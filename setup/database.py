
import sqlite3
import sys
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo

# DB_PATH = Path(__file__).resolve().with_name("vehicle_counter.db")
if getattr(sys, "frozen", False):
    BASE_DIR = Path(sys.executable).resolve().parent
else:
    BASE_DIR = Path(__file__).resolve().parent.parent

DB_PATH = BASE_DIR / "vehicle_counter.db"

TIMEZONE = ZoneInfo("Asia/Jakarta")


def now_local():
    return datetime.now(TIMEZONE)


def get_connection():
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout = 10000")
    return conn


def init_db():
    with get_connection() as conn:
        conn.execute("PRAGMA journal_mode = WAL")

        conn.execute("""
            CREATE TABLE IF NOT EXISTS vehicle_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_time TEXT NOT NULL,
                event_date TEXT NOT NULL,
                vehicle_type TEXT NOT NULL,
                direction TEXT NOT NULL
                    CHECK(direction IN ('Masuk', 'Keluar')),
                vehicle_id INTEGER
            )
        """)

        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_events_date
            ON vehicle_events(event_date)
        """)

        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_events_time
            ON vehicle_events(event_time)
        """)


def save_event(vehicle_type, direction, vehicle_id=None):
    event_datetime = now_local()
    event_time = event_datetime.isoformat(timespec="seconds")
    event_date = event_datetime.strftime("%Y-%m-%d")

    with get_connection() as conn:
        cursor = conn.execute("""
            INSERT INTO vehicle_events (
                event_time,
                event_date,
                vehicle_type,
                direction,
                vehicle_id
            )
            VALUES (?, ?, ?, ?, ?)
        """, (
            event_time,
            event_date,
            vehicle_type,
            direction,
            vehicle_id
        ))

        return {
            "id": cursor.lastrowid,
            "event_time": event_time,
            "event_date": event_date,
            "vehicle_type": vehicle_type,
            "direction": direction,
            "vehicle_id": vehicle_id
        }


def get_summary(event_date=None):
    if event_date is None:
        event_date = now_local().strftime("%Y-%m-%d")

    summary = {
        vehicle_type: {"Masuk": 0, "Keluar": 0}
        for vehicle_type in ["Mobil", "Motor", "Bus", "Truk"]
    }

    with get_connection() as conn:
        rows = conn.execute("""
            SELECT vehicle_type, direction, COUNT(*) AS total
            FROM vehicle_events
            WHERE event_date = ?
            GROUP BY vehicle_type, direction
        """, (event_date,)).fetchall()

    for row in rows:
        vehicle_type = row["vehicle_type"]
        direction = row["direction"]

        if vehicle_type in summary:
            summary[vehicle_type][direction] = row["total"]

    total_masuk = sum(v["Masuk"] for v in summary.values())
    total_keluar = sum(v["Keluar"] for v in summary.values())

    return {
        "date": event_date,
        "total_masuk": total_masuk,
        "total_keluar": total_keluar,
        "vehicles": summary
    }


# Buat tabel ketika modul diimpor
init_db()
