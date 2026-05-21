from fastapi import APIRouter, Query
from typing import Optional, List
from datetime import datetime, timedelta, date

from sqlalchemy import or_

from db.db import SessionLocal
from db.models import Screenshot
from services.minio.minio_reader import MinIOReader

router = APIRouter()
minio = MinIOReader()

# ================= BREAK TIME CONFIG =================
BREAK_TIMES = [
    ("06:54", "07:15"),
    ("11:00", "13:00"),
    ("15:00", "15:30"),
    ("17:30", "18:30"),
    ("22:45", "23:15"),
]

# ================= HELPER =================
def build_break_ranges(date_filter: date):
    ranges = []

    for start_str, end_str in BREAK_TIMES:
        start = datetime.combine(
            date_filter,
            datetime.strptime(start_str, "%H:%M").time()
        )
        end = datetime.combine(
            date_filter,
            datetime.strptime(end_str, "%H:%M").time()
        )

        ranges.append((start, end))

    return ranges


# ================= API =================
@router.get("/screenshots")
def get_screenshots(
    limit: int = Query(150, ge=1, le=1500),
    cam_id: Optional[str] = None,
    event_type: Optional[str] = None,
    date_filter: Optional[date] = None,
    mode: Optional[str] = Query("working")  # working | break | all
):
    db = SessionLocal()

    try:
        query = db.query(Screenshot)

        # ================= FILTER BASIC =================
        if cam_id:
            query = query.filter(Screenshot.cam_id == cam_id)

        if event_type:
            query = query.filter(Screenshot.event_type == event_type)

        # ================= FILTER DATE =================
        if date_filter:
            start_day = datetime.combine(date_filter, datetime.min.time())
            end_day = start_day + timedelta(days=1)

            query = query.filter(
                Screenshot.timestamp >= start_day,
                Screenshot.timestamp < end_day
            )

            # ================= MODE FILTER =================
            if mode != "all":
                break_ranges = build_break_ranges(date_filter)

                if mode == "break":
                    # INCLUDE hanya jam istirahat
                    conditions = [
                        (Screenshot.timestamp >= start) &
                        (Screenshot.timestamp <= end)
                        for start, end in break_ranges
                    ]

                    query = query.filter(or_(*conditions))

                elif mode == "working":
                    # EXCLUDE jam istirahat
                    for start, end in break_ranges:
                        query = query.filter(
                            ~(
                                (Screenshot.timestamp >= start) &
                                (Screenshot.timestamp <= end)
                            )
                        )

        # ================= FETCH =================
        rows = query.order_by(
            Screenshot.timestamp.desc()
        ).limit(limit).all()

        # ================= RESPONSE =================
        results: List[dict] = []

        for r in rows:
            results.append({
                "id": r.id,
                "cam_id": r.cam_id,
                "event_type": r.event_type,
                "path": minio.get_url(r.path),
                "timestamp": r.timestamp.isoformat() if r.timestamp else None,

                # 🔥 OPTIONAL FLAG (BIAR UI ENAK)
                "is_break": any(
                    start <= r.timestamp <= end
                    for start, end in build_break_ranges(r.timestamp.date())
                ) if r.timestamp else False
            })

        return {
            "mode": mode,
            "count": len(results),
            "results": results
        }

    finally:
        db.close()