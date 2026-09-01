from .base import MediaStore


class CloudStorageMediaStore(MediaStore):
    def __init__(self, bucket_name: str) -> None:
        try:
            from google.cloud import storage
        except ImportError as exc:
            raise RuntimeError("Install google-cloud-storage to use CloudStorageMediaStore") from exc
        self.client = storage.Client()
        self.bucket = self.client.bucket(bucket_name)

    def save(self, name: str, data: bytes, content_type: str) -> str:
        blob = self.bucket.blob(name)
        blob.upload_from_string(data, content_type=content_type)
        return f"gs://{self.bucket.name}/{name}"
