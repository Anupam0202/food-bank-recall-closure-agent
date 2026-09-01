from __future__ import annotations

import logging
from typing import Any

from app.domain.enums import IncidentState
from app.domain.exceptions import InvalidTransition
from app.domain.models import AuditEvent, Incident, new_id
from app.domain.state_machine import transition
from app.repositories.base import Repository

logger = logging.getLogger(__name__)


class AuditService:
    def __init__(self, repo: Repository) -> None:
        self.repo = repo

    def record(self, incident: Incident, event_type: str, message: str, **metadata: Any) -> AuditEvent:
        event = AuditEvent(
            id=new_id("audit"),
            incident_id=incident.id,
            correlation_id=incident.correlation_id,
            actor_type=metadata.pop("actor_type", "SYSTEM"),
            event_type=event_type,
            message=message,
            tool_name=metadata.pop("tool_name", None),
            model_name=metadata.pop("model_name", None),
            duration_ms=metadata.pop("duration_ms", None),
            payload_hash=metadata.pop("payload_hash", None),
            metadata=metadata,
        )
        self.repo.put("audit_events", event.id, event)
        logger.info(message, extra={
            "correlation_id": incident.correlation_id,
            "incident_id": incident.id,
            "event_type": event_type,
            "tool_name": event.tool_name,
            "duration_ms": event.duration_ms,
            "outcome": metadata.get("outcome", "recorded"),
            "retry_count": incident.attempt_count - 1,
        })
        return event

    def transition(self, incident: Incident, target: IncidentState) -> Incident:
        before = incident.state
        try:
            transition(incident, target)
        except InvalidTransition:
            self.record(
                incident,
                "STATE_TRANSITION_REJECTED",
                f"Rejected state transition {before} to {target}",
                state_before=str(before),
                state_after=str(target),
                outcome="rejected",
            )
            raise
        self.repo.put("incidents", incident.id, incident)
        self.record(
            incident,
            "STATE_TRANSITION",
            f"State transitioned from {before} to {target}",
            state_before=str(before),
            state_after=str(target),
            outcome="success",
        )
        return incident
