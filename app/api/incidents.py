from __future__ import annotations

import hashlib
import json

from fastapi import APIRouter, Header, HTTPException, Request, Response

from app.dependencies import container
from app.domain.enums import IncidentState
from app.security import require_admin, require_csrf
from app.services.evidence_pack_service import build_evidence_pack

router = APIRouter(prefix="/api")


@router.get("/incidents/{incident_id}")
def get_incident(incident_id: str):
    incident = container.repo.get("incidents", incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    matches = [match.to_dict() for match in container.repo.list("matches") if match.incident_id == incident_id]
    tasks = [task.to_dict() for task in container.repo.list("tasks") if task.incident_id == incident_id]
    audit = [event.to_dict() for event in container.repo.list("audit_events") if event.incident_id == incident_id]
    return {"incident": incident.to_dict(), "matches": matches, "tasks": tasks, "audit": audit}


@router.post("/incidents/{incident_id}/retry")
async def retry_incident(incident_id: str, request: Request, x_csrf_token: str | None = Header(default=None)):
    try:
        require_admin(request.session)
        require_csrf(request.session, x_csrf_token)
    except Exception as exc:
        raise HTTPException(status_code=403, detail="Administrator authentication and a valid CSRF token are required") from exc
    incident = container.repo.get("incidents", incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    if incident.state != IncidentState.FAILED_RETRYABLE:
        raise HTTPException(status_code=409, detail="Only FAILED_RETRYABLE incidents can be retried")
    recall = container.repo.get("recalls", incident.recall_id)
    source = container.repo.get("recall_sources", recall.source_id) if recall else None
    if not source or not recall:
        raise HTTPException(status_code=409, detail="Durable source checkpoint is incomplete")
    try:
        updated, _ = await container.workflow.process(source, recall)
        return updated.to_dict()
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Retry checkpoint was updated but processing did not complete") from exc


@router.get("/incidents/{incident_id}/export.json")
def export_incident(incident_id: str, request: Request):
    try:
        require_admin(request.session)
    except Exception as exc:
        raise HTTPException(status_code=403, detail="Administrator authentication is required for incident export") from exc
    payload = json.dumps(get_incident(incident_id), sort_keys=True, indent=2) + "\n"
    return Response(content=payload, media_type="application/json", headers={"Cache-Control": "no-store"})


@router.get("/incidents/{incident_id}/evidence-pack.zip")
def export_evidence_pack(incident_id: str, request: Request):
    """Download a privacy-minimized, tamper-evident closure packet."""
    try:
        require_admin(request.session)
    except Exception as exc:
        raise HTTPException(status_code=403, detail="Administrator authentication is required for evidence export") from exc
    try:
        payload, manifest = build_evidence_pack(container.repo, incident_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail="Incident not found") from exc
    filename = f"{incident_id}-evidence-pack.zip"
    return Response(
        content=payload,
        media_type="application/zip",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Cache-Control": "no-store",
            "X-Content-SHA256": hashlib.sha256(payload).hexdigest(),
            "X-Evidence-Finality": manifest["finality"],
            "X-Evidence-Root-SHA256": manifest["pack_root_sha256"],
        },
    )
