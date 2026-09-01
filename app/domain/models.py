from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any
from uuid import uuid4

from .enums import ConfidenceCategory, IncidentState, InventoryStatus, MatchCategory, TaskStatus


def utcnow() -> str:
    return datetime.now(UTC).isoformat()


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex[:12]}"


def _primitive(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, list):
        return [_primitive(v) for v in value]
    if isinstance(value, dict):
        return {k: _primitive(v) for k, v in value.items()}
    return value


class Serializable:
    def to_dict(self) -> dict[str, Any]:
        return _primitive(asdict(self))


@dataclass
class Agency(Serializable):
    id: str
    name: str
    location: str
    contact_label: str
    active: bool = True
    created_at: str = field(default_factory=utcnow)
    updated_at: str = field(default_factory=utcnow)


@dataclass
class RecallSource(Serializable):
    id: str
    provider: str
    source_url: str
    source_hash: str
    raw_payload: dict[str, Any] | str
    limitations: str
    retrieved_at: str = field(default_factory=utcnow)


@dataclass
class Recall(Serializable):
    id: str
    recall_number: str
    event_id: str
    classification: str
    product_description: str
    brands: list[str]
    upc_candidates: list[str]
    lot_codes: list[str]
    date_codes: list[str]
    reason: str
    distribution_pattern: str
    recalling_firm: str
    source_id: str
    created_at: str = field(default_factory=utcnow)
    updated_at: str = field(default_factory=utcnow)


@dataclass
class InventoryItem(Serializable):
    id: str
    agency_id: str
    name: str
    brand: str
    upc: str | None
    lot_code: str | None
    date_code: str | None
    quantity: int
    image_uri: str | None = None
    status: InventoryStatus = InventoryStatus.AVAILABLE
    original_values: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=utcnow)
    updated_at: str = field(default_factory=utcnow)


@dataclass
class Incident(Serializable):
    id: str
    idempotency_key: str
    recall_id: str
    state: IncidentState = IncidentState.RECEIVED
    attempt_count: int = 1
    exact_match_count: int = 0
    review_count: int = 0
    affected_agency_count: int = 0
    last_error: str | None = None
    correlation_id: str = field(default_factory=lambda: new_id("corr"))
    created_at: str = field(default_factory=utcnow)
    updated_at: str = field(default_factory=utcnow)


@dataclass
class MatchDecision(Serializable):
    id: str
    incident_id: str
    inventory_item_id: str
    category: MatchCategory
    matched_fields: list[str]
    confidence_category: ConfidenceCategory
    evidence: list[str]
    model_name: str | None = None
    human_resolution: str | None = None
    created_at: str = field(default_factory=utcnow)
    updated_at: str = field(default_factory=utcnow)


@dataclass
class PartnerTask(Serializable):
    id: str
    incident_id: str
    agency_id: str
    inventory_item_ids: list[str]
    required_action: str
    status: TaskStatus = TaskStatus.OPEN
    due_at: str | None = None
    acknowledged_by: str | None = None
    acknowledged_at: str | None = None
    resolution_note: str | None = None
    evidence_uri: str | None = None
    created_at: str = field(default_factory=utcnow)
    updated_at: str = field(default_factory=utcnow)


@dataclass
class AuditEvent(Serializable):
    id: str
    incident_id: str
    correlation_id: str
    actor_type: str
    event_type: str
    message: str
    tool_name: str | None = None
    model_name: str | None = None
    duration_ms: int | None = None
    payload_hash: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=utcnow)
