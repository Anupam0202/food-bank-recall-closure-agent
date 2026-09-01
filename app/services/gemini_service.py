from __future__ import annotations

import json
import logging
import re
import time
from dataclasses import dataclass
from io import BytesIO
from time import perf_counter
from typing import Any, Callable, TypeVar

from pydantic import ValidationError as PydanticValidationError

from app.agents.output_schemas import EvidenceSnippet, PackageAssessmentSchema, RecallExtraction
from app.agents.prompts import PACKAGE_PROMPT, extraction_prompt
from app.domain.exceptions import ModelSchemaError, TransientModelError

logger = logging.getLogger(__name__)
T = TypeVar("T")


@dataclass(frozen=True)
class ModelCallMetadata:
    mode: str
    model_name: str
    operation: str
    attempt_count: int
    duration_ms: int
    outcome: str


@dataclass(frozen=True)
class PackageAssessment:
    summary: str
    visible_identifiers: list[str]
    confidence: str
    evidence: list[dict[str, str]]
    requires_human_review: bool = True


class GeminiService:
    def __init__(self, mode: str, model_name: str, api_key: str | None = None, max_attempts: int = 3, sleep_fn: Callable[[float], None] = time.sleep) -> None:
        self.mode = mode.lower()
        self.model_name = model_name
        self.api_key = api_key
        self.max_attempts = max(1, min(max_attempts, 5))
        self.sleep_fn = sleep_fn
        self.last_call: ModelCallMetadata | None = None

    @staticmethod
    def _retryable(exc: Exception) -> bool:
        if isinstance(exc, ModelSchemaError):
            return True
        if isinstance(exc, (TimeoutError, ConnectionError, TransientModelError)):
            return True
        status = getattr(exc, "status_code", None) or getattr(exc, "code", None)
        return status in {408, 409, 429, 500, 502, 503, 504}

    def _run_with_retry(self, operation: str, call: Callable[[], T]) -> T:
        started = perf_counter()
        for attempt in range(1, self.max_attempts + 1):
            try:
                result = call()
                self.last_call = ModelCallMetadata(self.mode, self.model_name, operation, attempt, int((perf_counter() - started) * 1000), "success")
                logger.info("Model call completed", extra={"event_type": "model_call", "tool_name": operation, "duration_ms": self.last_call.duration_ms, "outcome": "success", "retry_count": attempt - 1, "ai_mode": self.mode})
                return result
            except Exception as exc:
                retry = self._retryable(exc) and attempt < self.max_attempts
                if not retry:
                    self.last_call = ModelCallMetadata(self.mode, self.model_name, operation, attempt, int((perf_counter() - started) * 1000), "error")
                    logger.warning("Model call failed", extra={"event_type": "model_call", "tool_name": operation, "duration_ms": self.last_call.duration_ms, "outcome": "error", "retry_count": attempt - 1, "error_category": type(exc).__name__, "ai_mode": self.mode})
                    raise
                self.sleep_fn(min(4.0, 0.25 * (2 ** (attempt - 1))))
        raise AssertionError("bounded retry loop exhausted unexpectedly")

    def extract_recall(self, raw: dict[str, Any] | str) -> RecallExtraction:
        if self.mode in {"mock", "replay"}:
            started = perf_counter()
            result = self._mock_extract(raw)
            outcome = "mocked" if self.mode == "mock" else "replayed"
            self.last_call = ModelCallMetadata(self.mode, self.model_name, "recall_extraction", 1, int((perf_counter() - started) * 1000), outcome)
            return result
        return self._run_with_retry("recall_extraction", lambda: self._live_extract_once(raw))

    def extract_document(self, data: bytes, content_type: str) -> RecallExtraction:
        if content_type == "application/json":
            return self.extract_recall(json.loads(data.decode("utf-8")))
        if content_type == "text/plain":
            return self.extract_recall(data.decode("utf-8"))
        if content_type != "application/pdf":
            raise ValueError("Unsupported recall document type")
        if self.mode in {"mock", "replay"}:
            from pypdf import PdfReader
            reader = PdfReader(BytesIO(data), strict=True)
            text = "\n".join(page.extract_text() or "" for page in reader.pages)
            return self.extract_recall(text)
        return self._run_with_retry("document_extraction", lambda: self._live_extract_bytes_once(data, content_type))

    def _mock_extract(self, raw: dict[str, Any] | str) -> RecallExtraction:
        if isinstance(raw, str):
            try:
                payload = json.loads(raw) if raw.strip().startswith("{") else None
            except json.JSONDecodeError:
                payload = None
            if payload is None:
                text = " ".join(raw.split())
                if not text:
                    raise ValueError("Recall text is empty")
                recall_match = re.search(r"(?:recall(?: number)?|reference)\s*[:#-]?\s*([A-Z0-9-]{4,})", text, re.I)
                upcs = re.findall(r"\b(?:\d[ -]?){11,13}\b", text)
                lots = re.findall(r"\b(?:lot(?: code)?\s*[:#-]?\s*)([A-Z0-9-]{4,})", text, re.I)
                ambiguities = ["Deterministic mock extraction is not a live Gemini result"]
                if not upcs: ambiguities.append("UPC missing")
                if not lots: ambiguities.append("Lot code missing")
                return RecallExtraction(
                    recall_number=(recall_match.group(1).upper() if recall_match else "MOCK-UNSTRUCTURED-001"),
                    event_id="MOCK-TEXT",
                    title="Uploaded recall notice",
                    classification="Unclassified",
                    product_description=text[:500],
                    reason="Review uploaded notice text",
                    upc_candidates=[re.sub(r"\D", "", value) for value in upcs],
                    lot_codes=[value.upper() for value in lots],
                    evidence=["Deterministic mock text extraction"],
                    source_passages=[EvidenceSnippet(field="product_description", quote=text[:240], source_location="uploaded text")],
                    ambiguities=ambiguities,
                    confidence_category="AMBIGUOUS",
                )
        else:
            payload = raw
        if not isinstance(payload, dict):
            raise ValueError("Recall extraction expects an object or text")
        recall_number = str(payload.get("recall_number") or "MOCK-UNNUMBERED")
        description = str(payload.get("product_description") or payload.get("title") or "Unspecified product")
        reason = str(payload.get("reason_for_recall") or payload.get("reason") or "Reason not supplied")
        evidence_values = list(payload.get("evidence") or [])
        passages = [EvidenceSnippet(field="product_description", quote=description[:240], source_location="structured source record")]
        ambiguities = list(payload.get("ambiguities") or [])
        if not payload.get("recall_number"): ambiguities.append("Recall number missing")
        if not payload.get("upc_candidates"): ambiguities.append("UPC candidates missing")
        if not payload.get("lot_codes"): ambiguities.append("Lot codes missing")
        return RecallExtraction(
            recall_number=recall_number,
            event_id=str(payload.get("event_id") or ""),
            title=str(payload.get("title") or description[:240]),
            classification=str(payload.get("classification") or "Unclassified"),
            product_description=description,
            brands=list(payload.get("brands") or []),
            upc_candidates=list(payload.get("upc_candidates") or []),
            lot_codes=list(payload.get("lot_codes") or []),
            date_codes=list(payload.get("date_codes") or []),
            reason=reason,
            distribution_pattern=str(payload.get("distribution_pattern") or "Not supplied"),
            recalling_firm=str(payload.get("recalling_firm") or "Not supplied"),
            evidence=evidence_values,
            source_passages=passages,
            ambiguities=ambiguities,
            confidence_category=str(payload.get("confidence_category") or ("SOURCE_EXACT" if payload.get("recall_number") and payload.get("upc_candidates") else "AMBIGUOUS")),
        )

    def _client_types(self):
        if not self.api_key:
            raise RuntimeError("GEMINI_API_KEY is required for live extraction")
        try:
            from google import genai
            from google.genai import types
        except ImportError as exc:
            raise RuntimeError("Install google-genai==2.20.0 for live extraction") from exc
        return genai.Client(api_key=self.api_key), types

    @staticmethod
    def _parse_response(response) -> RecallExtraction:
        try:
            if getattr(response, "parsed", None) is not None:
                return RecallExtraction.model_validate(response.parsed)
            return RecallExtraction.model_validate_json(response.text)
        except (PydanticValidationError, ValueError, TypeError) as exc:
            raise ModelSchemaError("Gemini response failed schema validation") from exc

    def _live_extract_once(self, raw: dict[str, Any] | str) -> RecallExtraction:
        client, types = self._client_types()
        source = json.dumps(raw, ensure_ascii=False) if isinstance(raw, dict) else raw
        response = client.models.generate_content(
            model=self.model_name,
            contents=extraction_prompt("text or JSON") + "\n" + source,
            config=types.GenerateContentConfig(response_mime_type="application/json", response_schema=RecallExtraction, temperature=0.1),
        )
        return self._parse_response(response)

    def _live_extract_bytes_once(self, data: bytes, content_type: str) -> RecallExtraction:
        client, types = self._client_types()
        response = client.models.generate_content(
            model=self.model_name,
            contents=[extraction_prompt(content_type), types.Part.from_bytes(data=data, mime_type=content_type)],
            config=types.GenerateContentConfig(response_mime_type="application/json", response_schema=RecallExtraction, temperature=0.1),
        )
        return self._parse_response(response)

    def assess_package_bytes(self, item_label: str, data: bytes, content_type: str) -> PackageAssessment:
        if self.mode in {"mock", "replay"}:
            started = perf_counter()
            outcome = "mocked" if self.mode == "mock" else "replayed"
            self.last_call = ModelCallMetadata(self.mode, self.model_name, "package_assessment", 1, int((perf_counter() - started) * 1000), outcome)
            return PackageAssessment(f"Package evidence for {item_label} remains a potential match requiring human review", [], "AMBIGUOUS", [])
        return self._run_with_retry("package_assessment", lambda: self._live_package_once(data, content_type))

    def _live_package_once(self, data: bytes, content_type: str) -> PackageAssessment:
        client, types = self._client_types()
        response = client.models.generate_content(
            model=self.model_name,
            contents=[PACKAGE_PROMPT, types.Part.from_bytes(data=data, mime_type=content_type)],
            config=types.GenerateContentConfig(response_mime_type="application/json", response_schema=PackageAssessmentSchema, temperature=0.1),
        )
        try:
            parsed = PackageAssessmentSchema.model_validate(response.parsed) if getattr(response, "parsed", None) is not None else PackageAssessmentSchema.model_validate_json(response.text)
        except (PydanticValidationError, ValueError, TypeError) as exc:
            raise ModelSchemaError("Gemini package response failed schema validation") from exc
        return PackageAssessment(parsed.summary, parsed.visible_identifiers, parsed.confidence, [item.model_dump() for item in parsed.evidence])

    def assess_package(self, item_label: str, image_path: str | None = None) -> PackageAssessment:
        if not image_path:
            return PackageAssessment("No image supplied", [], "MISSING", [])
        from pathlib import Path
        path = Path(image_path.removeprefix("file://"))
        mime = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".webp": "image/webp"}.get(path.suffix.lower())
        if not mime:
            raise ValueError("Unsupported package image type")
        return self.assess_package_bytes(item_label, path.read_bytes(), mime)
