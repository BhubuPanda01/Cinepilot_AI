"""Media storage for uploads and generated storyboard frames.

Cloud Run containers have an ephemeral, per-instance filesystem, so anything written
to local disk vanishes on restart and is invisible to other instances. When GCS_BUCKET
is set (as it is in production) objects go to Cloud Storage; otherwise this falls back
to local disk so local development works without a bucket.
"""

import logging
import os
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

BUCKET_NAME = os.environ.get("GCS_BUCKET")
LOCAL_MEDIA_DIR = Path(__file__).resolve().parent / "output_images"

_bucket = None


def using_gcs() -> bool:
    return bool(BUCKET_NAME)


def _get_bucket():
    global _bucket
    if _bucket is None:
        from google.cloud import storage as gcs

        _bucket = gcs.Client().bucket(BUCKET_NAME)
    return _bucket


def write_media(object_path: str, data: bytes, content_type: str = "image/png") -> None:
    """Store bytes at a logical path like 'uid/project_id/scene1_frame1.png'."""
    if using_gcs():
        _get_bucket().blob(object_path).upload_from_string(data, content_type=content_type)
        return

    local_path = LOCAL_MEDIA_DIR / object_path
    local_path.parent.mkdir(parents=True, exist_ok=True)
    local_path.write_bytes(data)


def read_media(object_path: str) -> Optional[bytes]:
    """Return stored bytes, or None if the object doesn't exist."""
    if using_gcs():
        blob = _get_bucket().blob(object_path)
        if not blob.exists():
            return None
        return blob.download_as_bytes()

    local_path = LOCAL_MEDIA_DIR / object_path
    return local_path.read_bytes() if local_path.exists() else None


def write_upload(object_path: str, data: bytes) -> None:
    """Archive an uploaded screenplay PDF. Best-effort: the pipeline reads the PDF
    from memory, so a failure here must never fail the request."""
    try:
        if using_gcs():
            _get_bucket().blob(object_path).upload_from_string(
                data, content_type="application/pdf"
            )
        else:
            local_path = Path(__file__).resolve().parent / "uploads" / Path(object_path).name
            local_path.parent.mkdir(parents=True, exist_ok=True)
            local_path.write_bytes(data)
    except Exception as e:
        logger.warning(
            "Could not archive upload %s: %s",
            object_path,
            e,
            extra={"event": "upload_archive_failed"},
        )
