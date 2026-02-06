# services/storage/minio_reader.py
import os
from datetime import timedelta
from minio import Minio

class MinIOReader:
    def __init__(self):
        self.client = Minio(
            os.getenv("MINIO_ENDPOINT"),
            access_key=os.getenv("MINIO_ACCESS_KEY"),
            secret_key=os.getenv("MINIO_SECRET_KEY"),
            secure=os.getenv("MINIO_SECURE", "false").lower() == "true"
        )
        self.bucket = os.getenv("MINIO_BUCKET", "bucket-computer-vision")

    def get_url(self, object_path: str) -> str:
        return self.client.presigned_get_object(
            bucket_name=self.bucket,
            object_name=object_path,
            expires=timedelta(minutes=10)
        )
