
from datetime import datetime, timedelta
from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from database import get_connection, get_summary, now_local

app = FastAPI(
    title="AI Vehicle Counter API",
    description="API penghitung kendaraan CCTV",
    version="1.0.0"
)

# Untuk pengembangan. Pada produksi, batasi ke domain FrontEnd Anda.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["GET"],
    allow_headers=["*"],
)


def validate_date(value):
    try:
        datetime.strptime(value, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Format tanggal harus YYYY-MM-DD"
        )


@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "service": "AI Vehicle Counter API",
        "date": now_local().strftime("%Y-%m-%d")
    }


@app.get("/api/summary")
def summary(date: str | None = None):
    if date is None:
        date = now_local().strftime("%Y-%m-%d")

    validate_date(date)
    return get_summary(date)


@app.get("/api/events")
def events(
    date: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    direction: str | None = Query(
        default=None, pattern="^(Masuk|Keluar)$"
    ),
    vehicle_type: str | None = Query(
        default=None, pattern="^(Mobil|Motor|Bus|Truk)$"
    ),
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0)
):
    if date and (start_date or end_date):
        raise HTTPException(
            status_code=400,
            detail="Gunakan date atau start_date/end_date, jangan keduanya"
        )

    if date:
        validate_date(date)
        start_date = date
        end_date = date
    else:
        if start_date:
            validate_date(start_date)
        if end_date:
            validate_date(end_date)

    if start_date and end_date and start_date > end_date:
        raise HTTPException(
            status_code=400,
            detail="start_date tidak boleh melebihi end_date"
        )

    sql = "SELECT * FROM vehicle_events WHERE 1=1"
    params = []

    if start_date:
        sql += " AND event_date >= ?"
        params.append(start_date)

    if end_date:
        sql += " AND event_date <= ?"
        params.append(end_date)

    if direction:
        sql += " AND direction = ?"
        params.append(direction)

    if vehicle_type:
        sql += " AND vehicle_type = ?"
        params.append(vehicle_type)

    sql += " ORDER BY id DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])

    with get_connection() as conn:
        rows = conn.execute(sql, params).fetchall()

    return {
        "count": len(rows),
        "limit": limit,
        "offset": offset,
        "data": [dict(row) for row in rows]
    }


@app.get("/api/daily")
def daily(
    start_date: str | None = None,
    end_date: str | None = None
):
    today = now_local().date()

    if not end_date:
        end_date = today.strftime("%Y-%m-%d")

    if not start_date:
        start_date = (today - timedelta(days=6)).strftime("%Y-%m-%d")

    validate_date(start_date)
    validate_date(end_date)

    if start_date > end_date:
        raise HTTPException(
            status_code=400,
            detail="start_date tidak boleh melebihi end_date"
        )

    with get_connection() as conn:
        rows = conn.execute("""
            SELECT
                event_date,
                direction,
                COUNT(*) AS total
            FROM vehicle_events
            WHERE event_date BETWEEN ? AND ?
            GROUP BY event_date, direction
            ORDER BY event_date
        """, (start_date, end_date)).fetchall()

    result = {}

    for row in rows:
        date = row["event_date"]

        if date not in result:
            result[date] = {"date": date, "masuk": 0, "keluar": 0}

        if row["direction"] == "Masuk":
            result[date]["masuk"] = row["total"]
        else:
            result[date]["keluar"] = row["total"]

    return {
        "start_date": start_date,
        "end_date": end_date,
        "data": list(result.values())
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)