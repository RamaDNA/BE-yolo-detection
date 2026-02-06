import cv2
import os
from datetime import datetime
from zoneinfo import ZoneInfo
from db.db import SessionLocal
from db.models import ScreenshotForTrain
from services.minio.minio_client import MinIOStorage

BASE_DIR = "/storage/screenshots-for-train"
WIB = ZoneInfo("Asia/Jakarta")
storage = MinIOStorage()

def save_event_for_train(cam_id: str, frame, event_type: str):
    """
    Save screenshot for training:
    - local file (legacy)
    - upload to MinIO (train)
    - metadata to DB
    """
    try:
        # 1️⃣ WIB timestamp
        now_wib = datetime.now(WIB)
        ts = now_wib.strftime("%Y%m%d_%H%M%S")

        # # 2️⃣ SAVE LOCAL (keep for now)
        # folder = os.path.join(BASE_DIR, cam_id)
        # os.makedirs(folder, exist_ok=True)

        # local_path = os.path.join(folder, f"{event_type}_{ts}.jpg")
        # cv2.imwrite(local_path, frame)

        # 3️⃣ Encode for MinIO
        success, buffer = cv2.imencode(".jpg", frame)
        if not success:
            return None

        image_bytes = buffer.tobytes()

        # 4️⃣ Upload to MinIO (train prefix)
        minio_path = storage.upload_image(
            image_bytes=image_bytes,
            cam_id=cam_id,
            event_type=event_type,
            purpose="train",
            ext="jpg"
        )

        # 5️⃣ Save metadata to DB
        db = SessionLocal()
        try:
            db_event = ScreenshotForTrain(
                cam_id=cam_id,
                event_type=event_type,
                path=minio_path,     # 🔑 simpan MinIO path
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
        print("save_event_for_train error:", e)
        return None
