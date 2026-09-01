from __future__ import annotations

import hashlib
import json

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse

from app.dependencies import container
from app.domain.exceptions import ModelSchemaError, TransientModelError, ValidationError
from app.domain.models import Recall, RecallSource, new_id
from app.services.pubsub_service import decode_pubsub_envelope
from app.services.recall_sources import OPENFDA_LIMITATION, source_from_payload

router = APIRouter()


def _verify_oidc(request: Request) -> None:
    audience = container.settings.pubsub_verification_audience
    if not audience:
        return
    header = request.headers.get("Authorization", "")
    if not header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Authenticated Pub/Sub push token required")
    try:
        from google.auth.transport import requests as google_requests
        from google.oauth2 import id_token
        id_token.verify_oauth2_token(header.removeprefix("Bearer "), google_requests.Request(), audience)
    except Exception as exc:
        raise HTTPException(status_code=401, detail="Invalid Pub/Sub push identity") from exc


def _terminal_poison(body: bytes, reason: Exception):
    digest = hashlib.sha256(body).hexdigest()
    source = RecallSource(f"source_{hashlib.sha256(f'PUBSUB_INVALID|{digest}'.encode()).hexdigest()[:20]}", "PUBSUB_INVALID", "pubsub://invalid", digest, {"byte_length": len(body)}, "Malformed source record retained only as a hash; no public alert action was taken.")
    incident = container.workflow.record_ingestion_failure(source, "UNPARSED-PUBSUB", reason, retryable=False)
    return JSONResponse(status_code=200, content={"status": "terminal_rejected", "retry": False, "incident_id": incident.id})


@router.post("/pubsub/recall")
async def pubsub_recall(request: Request):
    _verify_oidc(request)
    raw_body = await request.body()
    try:
        envelope = json.loads(raw_body.decode("utf-8"))
        decoded = decode_pubsub_envelope(envelope, container.settings.max_document_bytes)
    except Exception as exc:
        return _terminal_poison(raw_body, exc)

    payload = decoded.payload
    provider = str(payload.get("provider", "OPERATOR_EVENT"))
    source_url = str(payload.get("source_url", f"pubsub://{decoded.message_id}"))
    limitations = str(payload.get("limitations", OPENFDA_LIMITATION if provider == "OPENFDA" else "Operator-provided source record; verify against the current official notice."))
    source_payload = payload.get("record", payload)
    if not isinstance(source_payload, (dict, str)):
        return _terminal_poison(raw_body, ValidationError("Source record must be an object or text"))
    source = source_from_payload(source_payload, provider, source_url, limitations)
    try:
        extraction = container.gemini.extract_recall(source_payload)
        recall = Recall(
            id=new_id("recall"), recall_number=extraction.recall_number, event_id=extraction.event_id,
            classification=extraction.classification, product_description=extraction.product_description,
            brands=extraction.brands, upc_candidates=extraction.upc_candidates, lot_codes=extraction.lot_codes,
            date_codes=extraction.date_codes, reason=extraction.reason,
            distribution_pattern=extraction.distribution_pattern, recalling_firm=extraction.recalling_firm,
            source_id=source.id,
        )
        incident, created = await container.workflow.process(source, recall)
        return {"status": "processed", "incident_id": incident.id, "created": created, "delivery_attempt": decoded.delivery_attempt}
    except (TransientModelError, ModelSchemaError, TimeoutError, ConnectionError) as exc:
        container.workflow.record_ingestion_failure(source, str(payload.get("recall_number", "UNPARSED-PUBSUB")), exc, retryable=True)
        raise HTTPException(status_code=503, detail="Retryable workflow checkpoint recorded") from exc
    except Exception as exc:
        incident = container.workflow.record_ingestion_failure(source, str(payload.get("recall_number", "UNPARSED-PUBSUB")), exc, retryable=False)
        return {"status": "terminal_rejected", "retry": False, "incident_id": incident.id}
