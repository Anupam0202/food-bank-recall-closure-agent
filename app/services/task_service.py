from __future__ import annotations

from app.domain.enums import TaskStatus
from app.domain.models import PartnerTask, utcnow
from app.repositories.base import Repository
from app.workflows.idempotency import stable_id


class TaskService:
    def __init__(self, repo: Repository) -> None:
        self.repo = repo

    def create_partner_task(self, incident_id: str, agency_id: str, inventory_item_ids: list[str], required_action: str) -> PartnerTask:
        task_id = stable_id("task", incident_id, agency_id)
        existing = self.repo.get("tasks", task_id)
        if existing:
            return existing
        task = PartnerTask(task_id, incident_id, agency_id, sorted(set(inventory_item_ids)), required_action)
        self.repo.put("tasks", task.id, task)
        return task

    def acknowledge(self, task_id: str, actor: str, note: str = "") -> tuple[PartnerTask, bool]:
        task = self.repo.get("tasks", task_id)
        if not task:
            raise LookupError("Task not found")
        if task.status in {TaskStatus.ACKNOWLEDGED, TaskStatus.RESOLVED}:
            return task, False
        task.status = TaskStatus.ACKNOWLEDGED
        task.acknowledged_by = actor
        task.acknowledged_at = utcnow()
        task.resolution_note = note
        task.updated_at = utcnow()
        self.repo.put("tasks", task.id, task)
        return task, True

    def attach_evidence(self, task_id: str, evidence_uri: str) -> PartnerTask:
        task = self.repo.get("tasks", task_id)
        if not task:
            raise LookupError("Task not found")
        task.evidence_uri = evidence_uri
        task.updated_at = utcnow()
        self.repo.put("tasks", task.id, task)
        return task
