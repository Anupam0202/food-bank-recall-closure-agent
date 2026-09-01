from __future__ import annotations

import asyncio
import hashlib

from fastapi import APIRouter, File, Header, HTTPException, Request, UploadFile
from pydantic import BaseModel, Field

from app.dependencies import container
from app.security import require_admin, require_csrf, safe_filename, safe_public_error, validate_upload

router = APIRouter(prefix="/api")


class Acknowledgement(BaseModel):
    actor: str = Field(min_length=2, max_length=80)
    note: str = Field(default="", max_length=500)


class MatchResolution(BaseModel):
    resolution: str = Field(min_length=2, max_length=200)


def _authorize(request: Request, csrf: str | None):
    try:
        require_admin(request.session)
        require_csrf(request.session, csrf)
    except Exception as exc:
        raise HTTPException(status_code=403, detail="Administrator authentication and a valid CSRF token are required") from exc


@router.post("/tasks/{task_id}/acknowledge")
def acknowledge(task_id: str, body: Acknowledgement, request: Request, x_csrf_token: str | None = Header(default=None)):
    _authorize(request, x_csrf_token)
    try:
        return container.workflow.acknowledge_task(task_id, body.actor, body.note).to_dict()
    except LookupError as exc:
        raise HTTPException(status_code=404, detail="Partner task not found") from exc


@router.post("/tasks/{task_id}/evidence")
async def upload_task_evidence(task_id: str, request: Request, file: UploadFile = File(...), x_csrf_token: str | None = Header(default=None)):
    _authorize(request, x_csrf_token)
    task = container.repo.get("tasks", task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Partner task not found")
    data = await file.read(max(container.settings.max_image_bytes, container.settings.max_document_bytes) + 1)
    content_type = (file.content_type or "").split(";", 1)[0].lower()
    kind = "image" if content_type.startswith("image/") else "document"
    limit = container.settings.max_image_bytes if kind == "image" else container.settings.max_document_bytes
    try:
        validate_upload(data, content_type, kind, limit, file.filename)
        name = safe_filename(file.filename or "evidence")
        uri = await asyncio.to_thread(container.media.save, name, data, content_type)
        updated = container.workflow.attach_task_evidence(task_id, uri, hashlib.sha256(data).hexdigest())
        return updated.to_dict()
    except Exception as exc:
        raise HTTPException(status_code=422, detail=safe_public_error(exc)) from exc


@router.post("/matches/{match_id}/resolve")
def resolve(match_id: str, body: MatchResolution, request: Request, x_csrf_token: str | None = Header(default=None)):
    _authorize(request, x_csrf_token)
    try:
        return container.workflow.resolve_match(match_id, body.resolution).to_dict()
    except LookupError as exc:
        raise HTTPException(status_code=404, detail="Potential match not found") from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
