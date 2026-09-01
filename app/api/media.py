from __future__ import annotations

import re
from pathlib import Path

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import FileResponse

from app.dependencies import container
from app.security import require_admin

router = APIRouter()
LOCAL_MEDIA_ROOT = Path("runtime/uploads").resolve()
SAFE_OBJECT = re.compile(r"^[a-f0-9]{32}\.(pdf|json|txt|png|jpg|jpeg|webp)$")
MEDIA_TYPES = {
    ".pdf": "application/pdf",
    ".json": "application/json",
    ".txt": "text/plain; charset=utf-8",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".webp": "image/webp",
}


@router.get("/media/{object_name}", include_in_schema=False)
def private_local_media(object_name: str, request: Request):
    """Serve local development evidence only to an authenticated administrator."""
    try:
        require_admin(request.session)
    except Exception as exc:
        raise HTTPException(status_code=403, detail="Administrator authentication is required for private evidence") from exc
    if container.settings.use_cloud_storage:
        raise HTTPException(status_code=404, detail="Cloud evidence is not served by the local proxy")
    if not SAFE_OBJECT.fullmatch(object_name):
        raise HTTPException(status_code=404, detail="Evidence object not found")
    target = (LOCAL_MEDIA_ROOT / object_name).resolve()
    if target.parent != LOCAL_MEDIA_ROOT or not target.is_file():
        raise HTTPException(status_code=404, detail="Evidence object not found")
    return FileResponse(target, media_type=MEDIA_TYPES.get(target.suffix.lower(), "application/octet-stream"), filename=None)
