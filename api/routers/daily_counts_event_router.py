from sqlalchemy import func
from datetime import datetime, time
from zoneinfo import ZoneInfo
from typing import Optional
from db.db import SessionLocal
from db.models import Screenshot
from fastapi import APIRouter

router = APIRouter()

WIB = ZoneInfo("Asia/Jakarta")

@router.get("/screenshots/count-daily")
def get_daily_event_count(cam_id: Optional[str] = None):
    db = SessionLocal()
    try:
        # Ambil tanggal hari ini di WIB
        now_wib = datetime.now(WIB)
        today_wib = now_wib.date()

        # Buat datetime start hari ini WIB (00:00:00)
        start_of_day_wib = datetime.combine(today_wib, time.min, tzinfo=WIB)
        # Convert ke UTC karena timestamp di DB dalam UTC
        start_of_day_utc = start_of_day_wib.astimezone(ZoneInfo("UTC"))

        # Query
        query = db.query(
            Screenshot.event_type,
            func.count(Screenshot.id).label("total")
        ).filter(
            Screenshot.timestamp >= start_of_day_utc
        )

        if cam_id:
            query = query.filter(Screenshot.cam_id == cam_id)

        stats = query.group_by(Screenshot.event_type).all()
        results = {row[0] if row[0] else "unknown": row[1] for row in stats}

        return {
            "date": today_wib.isoformat(),
            "cam_id": cam_id or "all",
            "counts": results,
            "grand_total": sum(results.values())
        }
    finally:
        db.close()
