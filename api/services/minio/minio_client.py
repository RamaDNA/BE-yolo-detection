# services/storage/minio_client.py

import io
import os
from datetime import datetime
from zoneinfo import ZoneInfo
from minio import Minio

WIB = ZoneInfo("Asia/Jakarta")

class MinIOStorage:
    def __init__(self):
        self.client = Minio(
            os.getenv("MINIO_ENDPOINT"),
            access_key=os.getenv("MINIO_ACCESS_KEY"),
            secret_key=os.getenv("MINIO_SECRET_KEY"),
            secure=os.getenv("MINIO_SECURE", "false").lower() == "true"
        )
        self.bucket = os.getenv("MINIO_BUCKET", "bucket-computer-vision")

    def upload_image(
        self,
        image_bytes: bytes,
        cam_id: str,
        event_type: str,
        purpose: str = "evidence",  # 🔑 evidence | train
        ext: str = "jpg"
    ) -> str:
        """
        Structure:
        purpose/YYYY/MM/DD/cam_id/event_timestamp.jpg
        """
        if purpose not in ("evidence", "train"):
            raise ValueError("purpose must be 'evidence' or 'train'")

        if ext not in ("jpg", "png"):
            raise ValueError("ext must be 'jpg' or 'png'")
        
        now = datetime.now(WIB)

        filename = f"{event_type}_{int(now.timestamp()*1000)}.{ext}"
        object_path = (
            f"{purpose}/"
            f"{now.strftime('%Y/%m/%d')}/"
            f"{cam_id}/"
            f"{filename}"
        )

        content_type = "image/png" if ext == "png" else "image/jpeg"

        self.client.put_object(
            bucket_name=self.bucket,
            object_name=object_path,
            data=io.BytesIO(image_bytes),
            length=len(image_bytes),
            content_type=content_type
        )

        return object_path
