from __future__ import annotations

from collections import defaultdict

from app.agents.coordinator import AdkCoordinator
from app.domain.enums import IncidentState, InventoryStatus, MatchCategory
from app.domain.exceptions import ModelSchemaError, RetryableWorkflowError, TransientModelError, UnsafeActionError
from app.domain.models import Incident, MatchDecision, Recall, RecallSource, utcnow
from app.repositories.base import Repository
from app.services.audit_service import AuditService
from app.services.inventory_matcher import InventoryMatcher
from app.services.task_service import TaskService
from app.services.verification_service import VerificationService
from app.workflows.idempotency import incident_key, stable_id

REVIEW_CATEGORIES = {MatchCategory.IDENTIFIER_REVIEW, MatchCategory.SEMANTIC_OR_VISUAL_REVIEW, MatchCategory.INSUFFICIENT_DATA}


class RecallWorkflow:
    def __init__(self, repo: Repository, coordinator: AdkCoordinator, model_name: str, max_attempts: int = 3) -> None:
        self.repo = repo
        self.coordinator = coordinator
        self.model_name = model_name
        self.max_attempts = max_attempts
        self.matcher = InventoryMatcher()
        self.audit = AuditService(repo)
        self.tasks = TaskService(repo)
        self.verification = VerificationService()

    @staticmethod
    def idempotency_key(source: RecallSource, recall: Recall) -> str:
        return incident_key(source, recall)

    @staticmethod
    def _is_retryable(exc: Exception) -> bool:
        if isinstance(exc, (TransientModelError, ModelSchemaError, RetryableWorkflowError, TimeoutError, ConnectionError)):
            return True
        status = getattr(exc, "status_code", None) or getattr(exc, "code", None)
        return status in {408, 409, 429, 500, 502, 503, 504}

    async def process(self, source: RecallSource, recall: Recall) -> tuple[Incident, bool]:
        key = incident_key(source, recall)
        candidate = Incident(id=stable_id("incident", key), idempotency_key=key, recall_id=recall.id)
        create = getattr(self.repo, "create_if_absent", None)
        if create:
            incident, created = create("incidents", "idempotency_key", key, candidate.id, candidate)
        else:
            incident = self.repo.find_one("incidents", "idempotency_key", key)
            created = incident is None
            if created:
                incident = candidate
                self.repo.put("incidents", incident.id, incident)

        if not created:
            if incident.state == IncidentState.FAILED_RETRYABLE and incident.attempt_count < self.max_attempts:
                incident.attempt_count += 1
                recall.id = incident.recall_id
                self.repo.put("incidents", incident.id, incident)
                self.audit.record(incident, "RETRY_RESUMED", "Retryable workflow resumed from a durable checkpoint", outcome="retry", retry_count=incident.attempt_count - 1)
            else:
                self.audit.record(incident, "DUPLICATE_EVENT", "Duplicate source record returned the existing incident without duplicate actions", outcome="deduplicated")
                return incident, False

        try:
            await self._execute(incident, source, recall, created)
            return incident, created
        except Exception as exc:
            incident.last_error = f"{type(exc).__name__}: sanitized workflow failure"
            target = IncidentState.FAILED_RETRYABLE if self._is_retryable(exc) and incident.attempt_count < self.max_attempts else IncidentState.FAILED_TERMINAL
            if incident.state not in {IncidentState.FAILED_RETRYABLE, IncidentState.FAILED_TERMINAL, IncidentState.INTERNAL_CLOSED}:
                self.audit.transition(incident, target)
            self.repo.put("incidents", incident.id, incident)
            self.audit.record(incident, "WORKFLOW_FAILED", "Workflow stopped after recording a durable failure state", error_category=type(exc).__name__, retryable=target == IncidentState.FAILED_RETRYABLE, outcome="error")
            raise

    async def _execute(self, incident: Incident, source: RecallSource, recall: Recall, created: bool) -> None:
        self.repo.put("recall_sources", source.id, source)
        self.repo.put("recalls", recall.id, recall)
        if created:
            self.audit.record(incident, "INCIDENT_RECEIVED", "Source record received and idempotency key reserved", payload_hash=source.source_hash)

        self.audit.transition(incident, IncidentState.SOURCE_VALIDATED)
        self.audit.record(incident, "SOURCE_VALIDATED", "Source provenance, original payload, hash, and limitations were recorded")
        self.audit.transition(incident, IncidentState.EXTRACTED)
        self.audit.record(incident, "RECALL_EXTRACTED", "Structured recall fields passed schema validation", model_name=self.model_name, ai_mode=self.coordinator.mode)

        matches: list[MatchDecision] = []
        affected: dict[str, list[str]] = defaultdict(list)
        review: dict[str, list[str]] = defaultdict(list)
        inventory = self.repo.list("inventory")
        for item in inventory:
            decision = self.matcher.evaluate(recall, item)
            match = MatchDecision(
                id=stable_id("match", incident.id, item.id),
                incident_id=incident.id,
                inventory_item_id=item.id,
                category=decision.category,
                matched_fields=decision.matched_fields,
                confidence_category=decision.confidence,
                evidence=decision.evidence,
                model_name=self.model_name if decision.category == MatchCategory.SEMANTIC_OR_VISUAL_REVIEW else None,
            )
            matches.append(match)
            self.repo.put("matches", match.id, match)
            if decision.auto_quarantine:
                item.status = InventoryStatus.QUARANTINED
                item.updated_at = utcnow()
                self.repo.put("inventory", item.id, item)
                affected[item.agency_id].append(item.id)
                self.audit.record(incident, "QUARANTINE_HOLD_CREATED", "Exact identifiers created a reversible internal quarantine hold", inventory_item_id=item.id, matched_fields=decision.matched_fields)
            elif decision.category in REVIEW_CATEGORIES:
                item.status = InventoryStatus.HUMAN_REVIEW
                item.updated_at = utcnow()
                self.repo.put("inventory", item.id, item)
                review[item.agency_id].append(item.id)
                self.audit.record(incident, "HUMAN_REVIEW_REQUIRED", "Potential match routed to human review; no automatic quarantine was authorized", inventory_item_id=item.id, category=str(decision.category))

        incident.exact_match_count = sum(match.category == MatchCategory.EXACT_MATCH for match in matches)
        incident.review_count = sum(match.category in REVIEW_CATEGORIES for match in matches)
        incident.affected_agency_count = len(set(affected) | set(review))
        self.audit.transition(incident, IncidentState.MATCHED)
        self.audit.record(incident, "INVENTORY_MATCHED", "Deterministic-first inventory matching completed")

        for agency_id in sorted(set(affected) | set(review)):
            exact_ids, review_ids = affected.get(agency_id, []), review.get(agency_id, [])
            action = "Acknowledge quarantine hold" if exact_ids and not review_ids else "Review potential match and submit partner acknowledgement"
            task = self.tasks.create_partner_task(incident.id, agency_id, exact_ids + review_ids, action)
            self.audit.record(incident, "PARTNER_TASK_CREATED", "Partner action task created idempotently", task_id=task.id, agency_id=agency_id)
        if not affected and not review:
            task = self.tasks.create_partner_task(incident.id, "coordinator", [], "Confirm that no distributed inventory is affected")
            self.audit.record(incident, "COORDINATOR_CONFIRMATION_REQUIRED", "No-match outcome still requires human acknowledgement", task_id=task.id)

        self.audit.transition(incident, IncidentState.ACTIONED)
        self.audit.record(incident, "ACTIONS_CREATED", "Reversible holds and partner tasks were durably recorded")
        current_tasks = [task for task in self.repo.list("tasks") if task.incident_id == incident.id]
        result = await self.coordinator.summarize(incident.to_dict(), [match.to_dict() for match in matches], [task.to_dict() for task in current_tasks])
        self.audit.record(incident, "ADK_COORDINATOR", result.summary, model_name=self.model_name, tool_name="RecallCoordinatorAgent", duration_ms=result.duration_ms, outcome=result.outcome, ai_mode=result.mode)
        self.audit.transition(incident, IncidentState.AWAITING_ACK)

    def record_ingestion_failure(self, source: RecallSource, recall_number: str, exc: Exception, retryable: bool) -> Incident:
        recall_id = stable_id("recall", source.source_hash)
        recall = Recall(recall_id, recall_number or "UNPARSED", "", "Unclassified", "Source extraction failed; manual review required", [], [], [], [], "Extraction failed", "Not supplied", "Not supplied", source.id)
        key = incident_key(source, recall)
        incident = Incident(stable_id("incident", key), key, recall.id)
        existing, created = self.repo.create_if_absent("incidents", "idempotency_key", key, incident.id, incident)
        incident = existing
        if created:
            self.repo.put("recall_sources", source.id, source)
            self.repo.put("recalls", recall.id, recall)
            self.audit.record(incident, "INCIDENT_RECEIVED", "Source record retained after extraction failure", payload_hash=source.source_hash)
            incident.last_error = f"{type(exc).__name__}: sanitized ingestion failure"
            self.audit.transition(incident, IncidentState.FAILED_RETRYABLE if retryable else IncidentState.FAILED_TERMINAL)
            self.audit.record(incident, "EXTRACTION_FAILED", "Structured extraction failed; source preserved for manual review", error_category=type(exc).__name__, retryable=retryable, outcome="error")
        return incident

    def resolve_match(self, match_id: str, resolution: str) -> MatchDecision:
        match = self.repo.get("matches", match_id)
        if not match:
            raise LookupError("Match not found")
        normalized = " ".join(resolution.lower().split())
        forbidden = ("dispose", "destroy", "safe to eat", "safe for consumption", "declare safe")
        if any(term in normalized for term in forbidden):
            incident = self.repo.get("incidents", match.incident_id)
            self.audit.record(incident, "UNSAFE_ACTION_REJECTED", "A prohibited disposition or safety claim was rejected", actor_type="HUMAN", outcome="rejected")
            raise UnsafeActionError("This application never authorizes disposal or declares product safety")
        match.human_resolution = resolution
        match.updated_at = utcnow()
        self.repo.put("matches", match.id, match)
        positive = ("confirmed affected", "recalled lot present", "match confirmed")
        negative = ("not affected", "not present", "no recalled", "does not match")
        confirmed_affected = any(term in normalized for term in positive) and not any(term in normalized for term in negative)
        item = self.repo.get("inventory", match.inventory_item_id)
        if confirmed_affected and item:
            item.status = InventoryStatus.QUARANTINED
            item.updated_at = utcnow()
            self.repo.put("inventory", item.id, item)
        incident = self.repo.get("incidents", match.incident_id)
        self.audit.record(incident, "HUMAN_REVIEW_RESOLVED", "A human recorded the potential-match review outcome", actor_type="HUMAN", confirmed_affected=confirmed_affected)
        self.try_close(incident.id)
        return match

    def acknowledge_task(self, task_id: str, actor: str, note: str = ""):
        task, changed = self.tasks.acknowledge(task_id, actor, note)
        if changed:
            incident = self.repo.get("incidents", task.incident_id)
            self.audit.record(incident, "PARTNER_ACKNOWLEDGEMENT", f"Partner task acknowledged by {actor}", actor_type="HUMAN", task_id=task.id)
            self.try_close(incident.id)
        return task

    def attach_task_evidence(self, task_id: str, evidence_uri: str, payload_hash: str):
        task = self.tasks.attach_evidence(task_id, evidence_uri)
        incident = self.repo.get("incidents", task.incident_id)
        self.audit.record(incident, "TASK_EVIDENCE_RECORDED", "Partner evidence was stored privately", actor_type="HUMAN", task_id=task.id, payload_hash=payload_hash)
        return task

    def try_close(self, incident_id: str) -> tuple[Incident, list[str]]:
        incident = self.repo.get("incidents", incident_id)
        if not incident:
            raise LookupError("Incident not found")
        if incident.state == IncidentState.INTERNAL_CLOSED:
            return incident, []
        matches = [match for match in self.repo.list("matches") if match.incident_id == incident_id]
        tasks = [task for task in self.repo.list("tasks") if task.incident_id == incident_id]
        blockers = self.verification.closure_blockers(matches, tasks, self.repo.list("inventory"))
        if blockers:
            self.audit.record(incident, "CLOSURE_BLOCKED", "Internal operational closure remains blocked", blockers=blockers, outcome="blocked")
            return incident, blockers
        if incident.state in {IncidentState.ACTIONED, IncidentState.ESCALATED}:
            self.audit.transition(incident, IncidentState.AWAITING_ACK)
        if incident.state == IncidentState.AWAITING_ACK:
            self.audit.transition(incident, IncidentState.VERIFIED)
        if incident.state == IncidentState.VERIFIED:
            self.audit.transition(incident, IncidentState.INTERNAL_CLOSED)
            self.audit.record(incident, "INTERNAL_CLOSED", "Internal operational closure completed; official recall status remains unchanged", outcome="success")
        return incident, []
