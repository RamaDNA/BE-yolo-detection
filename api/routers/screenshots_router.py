from fastapi import APIRouter, Query
from typing import Optional, List
from db.db import SessionLocal
from db.models import Screenshot
from services.minio.minio_reader import MinIOReader

router = APIRouter()
minio = MinIOReader()


@router.get("/screenshots")
def get_screenshots(
    limit: int = Query(150, ge=1, le=400),
    cam_id: Optional[str] = None,
    event_type: Optional[str] = None
):
    db = SessionLocal()
    try:
        query = db.query(Screenshot)

        if cam_id:
            query = query.filter(Screenshot.cam_id == cam_id)
        if event_type:
            query = query.filter(Screenshot.event_type == event_type)

        rows = query.order_by(Screenshot.timestamp.desc()).limit(limit).all()

        results: List[dict] = []
        for r in rows:
            results.append({
                "id": r.id,
                "cam_id": r.cam_id,
                "event_type": r.event_type,
                "path": minio.get_url(r.path),  # presigned URL
                "timestamp": r.timestamp.isoformat() if r.timestamp else None,
            })

        return {"count": len(results), "results": results}
    finally:
        db.close()