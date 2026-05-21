from datetime import datetime, time, date, timedelta
from zoneinfo import ZoneInfo
from typing import Optional
from fastapi import APIRouter, Query
from sqlalchemy import func, or_, and_

from db.db import SessionLocal
from db.models import Screenshot

router = APIRouter()

WIB = ZoneInfo("Asia/Jakarta")
UTC = ZoneInfo("UTC")

# ================= BREAK TIME =================
BREAK_TIMES = [
    ("06:54", "07:15"),
    ("11:00", "13:00"),
    ("15:00", "15:30"),
    ("17:30", "18:30"),
    ("22:45", "23:15"),
]

# ================= HELPER =================
def build_break_ranges_wib(date_filter: date):
    ranges = []

    for start_str, end_str in BREAK_TIMES:
        start = datetime.combine(
            date_filter,
            datetime.strptime(start_str, "%H:%M").time(),
            tzinfo=WIB
        )
        end = datetime.combine(
            date_filter,
            datetime.strptime(end_str, "%H:%M").time(),
            tzinfo=WIB
        )

        ranges.append((
            start.astimezone(UTC),
            end.astimezone(UTC)
        ))

    return ranges


# ================= API =================
@router.get("/screenshots/count-daily")
def get_event_count(
    date_filter: Optional[date] = Query(None),
    cam_id: Optional[str] = None,
    mode: Optional[str] = Query("working"),   # working | break | all
    period: Optional[str] = Query("daily")    # daily | monthly | yearly
):
    db = SessionLocal()

    try:
        # ================= DEFAULT DATE =================
        if not date_filter:
            now_wib = datetime.now(WIB)
            date_filter = now_wib.date()

        # ================= RANGE WIB =================
        if period == "daily":
            start_wib = datetime.combine(date_filter, time.min, tzinfo=WIB)
            end_wib = datetime.combine(date_filter, time.max, tzinfo=WIB)

        elif period == "monthly":
            start_wib = datetime(date_filter.year, date_filter.month, 1, tzinfo=WIB)

            if date_filter.month == 12:
                end_wib = datetime(date_filter.year + 1, 1, 1, tzinfo=WIB)
            else:
                end_wib = datetime(date_filter.year, date_filter.month + 1, 1, tzinfo=WIB)

        elif period == "yearly":
            start_wib = datetime(date_filter.year, 1, 1, tzinfo=WIB)
            end_wib = datetime(date_filter.year + 1, 1, 1, tzinfo=WIB)

        else:
            raise ValueError("Invalid period")

        # ================= CONVERT UTC =================
        start_utc = start_wib.astimezone(UTC)
        end_utc = end_wib.astimezone(UTC)

        # ================= BASE QUERY =================
        query = db.query(
            Screenshot.event_type,
            func.count(Screenshot.id).label("total")
        ).filter(
            Screenshot.timestamp >= start_utc,
            Screenshot.timestamp < end_utc
        )

        if cam_id:
            query = query.filter(Screenshot.cam_id == cam_id)

        # ================= MODE FILTER =================
        if mode != "all":

            # ===== DAILY
            if period == "daily":
                break_ranges = build_break_ranges_wib(date_filter)

                if mode == "break":
                    conditions = [
                        and_(
                            Screenshot.timestamp >= start,
                            Screenshot.timestamp <= end
                        )
                        for start, end in break_ranges
                    ]
                    query = query.filter(or_(*conditions))

                elif mode == "working":
                    for start, end in break_ranges:
                        query = query.filter(
                            ~and_(
                                Screenshot.timestamp >= start,
                                Screenshot.timestamp <= end
                            )
                        )

            # ===== MONTHLY
            elif period == "monthly":
                current_date = start_wib.date()
                end_date = (end_wib - timedelta(days=1)).date()

                all_break_conditions = []

                while current_date <= end_date:
                    daily_ranges = build_break_ranges_wib(current_date)

                    for start, end in daily_ranges:
                        all_break_conditions.append(
                            and_(
                                Screenshot.timestamp >= start,
                                Screenshot.timestamp <= end
                            )
                        )

                    current_date += timedelta(days=1)

                if mode == "break":
                    query = query.filter(or_(*all_break_conditions))

                elif mode == "working":
                    for cond in all_break_conditions:
                        query = query.filter(~cond)

            # ===== YEARLY (FIX 🔥)
            elif period == "yearly":
                current_date = start_wib.date()
                end_date = (end_wib - timedelta(days=1)).date()

                all_break_conditions = []

                while current_date <= end_date:
                    daily_ranges = build_break_ranges_wib(current_date)

                    for start, end in daily_ranges:
                        all_break_conditions.append(
                            and_(
                                Screenshot.timestamp >= start,
                                Screenshot.timestamp <= end
                            )
                        )

                    current_date += timedelta(days=1)

                if mode == "break":
                    query = query.filter(or_(*all_break_conditions))

                elif mode == "working":
                    for cond in all_break_conditions:
                        query = query.filter(~cond)

        # ================= GROUP =================
        stats = query.group_by(Screenshot.event_type).all()

        results = {
            row[0] if row[0] else "unknown": row[1]
            for row in stats
        }

        return {
            "date": date_filter.isoformat(),
            "period": period,
            "mode": mode,
            "cam_id": cam_id or "all",
            "counts": results,
            "grand_total": sum(results.values())
        }

    finally:
        db.close()