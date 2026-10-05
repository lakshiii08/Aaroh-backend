import os
import shutil
from pathlib import Path
from typing import BinaryIO, Optional
from app.storage.base import BaseStorage
from app.core.config import settings
from app.core.logging import logger

class S3CompatibleStorage(BaseStorage):
    def __init__(self):
        self.bucket = settings.S3_BUCKET
        self.endpoint = settings.S3_ENDPOINT
        self.local_dir = Path(settings.LOCAL_STORAGE_DIR)
        self.local_dir.mkdir(parents=True, exist_ok=True)
        self.s3_client = self._init_s3_client()

    def _init_s3_client(self):
        if settings.AWS_ACCESS_KEY_ID and settings.AWS_SECRET_ACCESS_KEY:
            try:
                import boto3
                return boto3.client(
                    "s3",
                    region_name=settings.AWS_REGION,
                    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                    endpoint_url=settings.S3_ENDPOINT,
                )
            except Exception as e:
                logger.warning(f"Could not connect to S3 ({e}). Using local storage at {self.local_dir}")
        return None

    def upload_file(self, file_obj: BinaryIO, destination_path: str, content_type: Optional[str] = None) -> str:
        if self.s3_client:
            try:
                extra_args = {"ContentType": content_type} if content_type else {}
                self.s3_client.upload_fileobj(file_obj, self.bucket, destination_path, ExtraArgs=extra_args)
                return f"s3://{self.bucket}/{destination_path}"
            except Exception as e:
                logger.warning(f"S3 upload failed ({e}). Falling back to local storage.")

        target = self.local_dir / destination_path
        target.parent.mkdir(parents=True, exist_ok=True)
        with open(target, "wb") as f:
            shutil.copyfileobj(file_obj, f)
        return str(target)

    def download_file(self, source_path: str, local_destination: str) -> str:
        if self.s3_client and source_path.startswith("s3://"):
            key = source_path.replace(f"s3://{self.bucket}/", "")
            self.s3_client.download_file(self.bucket, key, local_destination)
            return local_destination

        target = self.local_dir / source_path
        if target.exists():
            shutil.copy(target, local_destination)
            return local_destination
        raise FileNotFoundError(f"Source file '{source_path}' not found in storage.")

    def file_exists(self, file_path: str) -> bool:
        if self.s3_client and file_path.startswith("s3://"):
            try:
                key = file_path.replace(f"s3://{self.bucket}/", "")
                self.s3_client.head_object(Bucket=self.bucket, Key=key)
                return True
            except Exception:
                return False
        return (self.local_dir / file_path).exists()

storage_client = S3CompatibleStorage()
