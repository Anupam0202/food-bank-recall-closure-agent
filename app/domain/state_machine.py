from __future__ import annotations

from .enums import ALLOWED_TRANSITIONS, IncidentState, MatchCategory, TaskStatus
from .exceptions import InvalidTransition
from .models import Incident, MatchDecision, PartnerTask, utcnow


def transition(incident: Incident, target: IncidentState) -> Incident:
    if target == incident.state:
        return incident
    allowed = ALLOWED_TRANSITIONS.get(incident.state, set())
    if target not in allowed:
        raise InvalidTransition(f"Cannot transition {incident.state} to {target}")
    incident.state = target
    incident.updated_at = utcnow()
    return incident


def closure_blockers(matches: list[MatchDecision], tasks: list[PartnerTask]) -> list[str]:
    blockers: list[str] = []
    unresolved = [m for m in matches if m.category in {
        MatchCategory.IDENTIFIER_REVIEW,
        MatchCategory.SEMANTIC_OR_VISUAL_REVIEW,
        MatchCategory.INSUFFICIENT_DATA,
    } and not m.human_resolution]
    if unresolved:
        blockers.append(f"{len(unresolved)} review match(es) unresolved")
    open_tasks = [t for t in tasks if t.status not in {TaskStatus.ACKNOWLEDGED, TaskStatus.RESOLVED}]
    if open_tasks:
        blockers.append(f"{len(open_tasks)} partner task(s) unacknowledged")
    return blockers
