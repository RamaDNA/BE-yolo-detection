from fastapi import APIRouter, HTTPException, Query
from minio.error import S3Error
from services.minio.minio_reader import MinIOReader
import traceback

router = APIRouter(prefix="/api", tags=["MinIO"])
reader = MinIOReader()

@router.get("/evidence-url")
def get_evidence_url(
    path: str = Query(
        ...,
        examples={
            "sample": {
                "summary": "Contoh path evidence",
                "value": "evidence/2026/02/04/cam1/no_glove_1770171465721.jpg"
            }
        }
    )
):
    # basic safety
    if ".." in path or path.startswith("/"):
        raise HTTPException(status_code=400, detail="Invalid path")

    try:
        url = reader.presigned_url(path)
        return {
            "path": path,
            "url": url
        }

    except S3Error as e:
        raise HTTPException(status_code=404, detail=str(e))

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
