from __future__ import annotations

import asyncio
import hashlib
import json

from fastapi import APIRouter, File, Form, Header, HTTPException, Request, UploadFile
from pydantic import BaseModel, Field

from app.dependencies import container
from app.domain.enums import MatchCategory
from app.domain.exceptions import ModelSchemaError, TransientModelError
from app.domain.models import AuditEvent, Recall, RecallSource, new_id
from app.security import require_admin, require_csrf, safe_filename, safe_public_error, validate_upload
from app.services.recall_sources import OPENFDA_LIMITATION, fetch_openfda_by_recall_number, source_from_payload

router = APIRouter(prefix="/api")


def _authorize(request: Request, csrf: str | None):
    try:
        require_admin(request.session)
        require_csrf(request.session, csrf)
    except Exception as exc:
        raise HTTPException(status_code=403, detail="Administrator authentication and a valid CSRF token are required") from exc


def _recall(extraction, source_id: str) -> Recall:
    return Recall(
        id=new_id("recall"), recall_number=extraction.recall_number, event_id=extraction.event_id,
        classification=extraction.classification, product_description=extraction.product_description,
        brands=extraction.brands, upc_candidates=extraction.upc_candidates, lot_codes=extraction.lot_codes,
        date_codes=extraction.date_codes, reason=extraction.reason,
        distribution_pattern=extraction.distribution_pattern, recalling_firm=extraction.recalling_firm,
        source_id=source_id,
    )


@router.post("/recalls/upload")
@router.post("/recalls/ingest", include_in_schema=False)
async def upload_recall(
    request: Request,
    file: UploadFile = File(...),
    source_url: str = Form(default="operator://upload"),
    x_csrf_token: str | None = Header(default=None),
):
    _authorize(request, x_csrf_token)
    data = await file.read(container.settings.max_document_bytes + 1)
    content_type = (file.content_type or "").split(";", 1)[0].lower()
    try:
        validate_upload(data, content_type, "document", container.settings.max_document_bytes, file.filename)
    except Exception as exc:
        raise HTTPException(status_code=422, detail=safe_public_error(exc)) from exc
    stored_name = safe_filename(file.filename or "recall")
    try:
        media_uri = await asyncio.to_thread(container.media.save, stored_name, data, content_type)
    except Exception as exc:
        raise HTTPException(status_code=503, detail="The source record could not be stored durably") from exc
    raw_metadata: dict[str, object] = {"media_uri": media_uri, "stored_name": stored_name, "content_type": content_type, "byte_length": len(data)}
    if content_type == "text/plain":
        raw_metadata["source_text"] = data.decode("utf-8")
    elif content_type == "application/json":
        raw_metadata["source_json"] = json.loads(data.decode("utf-8"))
    source_digest = hashlib.sha256(data).hexdigest()
    source = RecallSource(
        id=f"source_{hashlib.sha256(f'OPERATOR_UPLOAD|{source_digest}'.encode()).hexdigest()[:20]}", provider="OPERATOR_UPLOAD", source_url=source_url,
        source_hash=source_digest, raw_payload=raw_metadata,
        limitations="Operator-provided source record. Confirm against the current official recall notice.",
    )
    try:
        extraction = await asyncio.to_thread(container.gemini.extract_document, data, content_type)
        incident, created = await container.workflow.process(source, _recall(extraction, source.id))
        return {"incident": incident.to_dict(), "created": created, "media_uri": media_uri, "ai_mode": container.settings.ai_label}
    except Exception as exc:
        retryable = isinstance(exc, (TransientModelError, ModelSchemaError, TimeoutError, ConnectionError))
        incident = container.workflow.record_ingestion_failure(source, "UNPARSED-UPLOAD", exc, retryable)
        status = 503 if retryable else 422
        raise HTTPException(status_code=status, detail=f"Extraction failed safely; incident {incident.id} was preserved for manual review") from exc


class RecallImportRequest(BaseModel):
    recall_number: str = Field(min_length=3, max_length=80)
    provider: str = Field(default="OPENFDA", pattern="^OPENFDA$")


@router.post("/recalls/import")
@router.post("/recalls/import-openfda", include_in_schema=False)
async def import_recall(body: RecallImportRequest, request: Request, x_csrf_token: str | None = Header(default=None)):
    _authorize(request, x_csrf_token)
    try:
        imported = await asyncio.to_thread(fetch_openfda_by_recall_number, body.recall_number)
        record = imported["record"]
        source = source_from_payload(record, "OPENFDA", imported["source_url"], OPENFDA_LIMITATION)
        extraction = await asyncio.to_thread(container.gemini.extract_recall, record)
        incident, created = await container.workflow.process(source, _recall(extraction, source.id))
        return {"incident": incident.to_dict(), "created": created, "source_limitation": OPENFDA_LIMITATION}
    except LookupError as exc:
        raise HTTPException(status_code=404, detail="No matching openFDA source record was found") from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail="The fixed-domain openFDA import could not be completed") from exc


@router.post("/inventory/{item_id}/package-evidence")
async def package_evidence(
    item_id: str,
    request: Request,
    file: UploadFile = File(...),
    x_csrf_token: str | None = Header(default=None),
):
    _authorize(request, x_csrf_token)
    item = container.repo.get("inventory", item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Inventory item not found")
    data = await file.read(container.settings.max_image_bytes + 1)
    content_type = (file.content_type or "").split(";", 1)[0].lower()
    try:
        validate_upload(data, content_type, "image", container.settings.max_image_bytes, file.filename)
        name = safe_filename(file.filename or "package.png")
        uri = await asyncio.to_thread(container.media.save, name, data, content_type)
        assessment = await asyncio.to_thread(container.gemini.assess_package_bytes, item.name, data, content_type)
    except Exception as exc:
        raise HTTPException(status_code=422, detail=safe_public_error(exc)) from exc
    item.image_uri = uri
    container.repo.put("inventory", item.id, item)
    related = [match for match in container.repo.list("matches") if match.inventory_item_id == item.id]
    for match in related:
        match.evidence.append(f"Package observation: {assessment.summary}")
        if match.category != MatchCategory.EXACT_MATCH:
            match.category = MatchCategory.SEMANTIC_OR_VISUAL_REVIEW
        container.repo.put("matches", match.id, match)
        incident = container.repo.get("incidents", match.incident_id)
        event = AuditEvent(
            id=new_id("audit"), incident_id=incident.id, correlation_id=incident.correlation_id,
            actor_type="HUMAN+MODEL", event_type="PACKAGE_EVIDENCE_RECORDED",
            message="Package image stored; model observation remains a potential match requiring human review",
            model_name=container.settings.model_name, payload_hash=hashlib.sha256(data).hexdigest(),
            metadata={"media_uri": uri, "confidence": assessment.confidence, "ai_mode": container.settings.ai_label},
        )
        container.repo.put("audit_events", event.id, event)
    return {"media_uri": uri, "assessment": assessment.__dict__, "requires_human_review": True, "ai_mode": container.settings.ai_label}
