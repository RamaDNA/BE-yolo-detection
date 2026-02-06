import cv2
import os
from datetime import datetime
from zoneinfo import ZoneInfo
from db.db import SessionLocal
from db.models import Screenshot
from services.minio.minio_client import MinIOStorage

BASE_DIR = "/storage/screenshots"
WIB = ZoneInfo("Asia/Jakarta")
storage = MinIOStorage()

def save_event(cam_id: str, frame, event_type: str):
    """
    Save screenshot:
    - local file (legacy)
    - upload to MinIO (new)
    - metadata to DB
    """
    try:
        #  WIB timestamp
        now_wib = datetime.now(WIB)
        ts = now_wib.strftime("%Y%m%d_%H%M%S")

        # #  SAVE LOCAL (legacy – keep)
        # folder = os.path.join(BASE_DIR, cam_id)
        # os.makedirs(folder, exist_ok=True)

        # local_path = os.path.join(folder, f"{event_type}_{ts}.jpg")
        # cv2.imwrite(local_path, frame)

        #  Encode for MinIO
        success, buffer = cv2.imencode(".jpg", frame)
        if not success:
            return None

        image_bytes = buffer.tobytes()

        #  Upload to MinIO (evidence)
        minio_path = storage.upload_image(
            image_bytes=image_bytes,
            cam_id=cam_id,
            event_type=event_type,
            purpose="evidence",
            ext="jpg"
        )

        #  Save metadata to DB
        db = SessionLocal()
        try:
            db_event = Screenshot(
                cam_id=cam_id,
                event_type=event_type,
                path=minio_path,     # 🔑 simpan path MinIO
                timestamp=now_wib
            )
            db.add(db_event)
            db.commit()
            db.refresh(db_event)
        except Exception as e:
            db.rollback()
            print("DB error:", e)
        finally:
            db.close()

        return {
            "minio_path": minio_path
        }

    except Exception as e:
        print("save_event error:", e)
        return None
