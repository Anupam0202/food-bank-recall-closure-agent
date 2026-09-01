#!/usr/bin/env python3
from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.agents.coordinator import AdkCoordinator
from app.domain.enums import InventoryStatus, MatchCategory
from app.repositories.memory import InMemoryRepository
from app.services.demo_data import seed_demo
from app.services.gemini_service import GeminiService
from app.workflows.recall_workflow import RecallWorkflow


async def main():
    repo = InMemoryRepository()
    gemini = GeminiService("mock", "gemini-3.7-flash")
    workflow = RecallWorkflow(repo, AdkCoordinator("mock", "gemini-3.7-flash"), "gemini-3.7-flash")
    source, recall = seed_demo(repo, gemini)
    incident, created = await workflow.process(source, recall)
    duplicate, duplicate_created = await workflow.process(source, recall)

    review_match = next(m for m in repo.list("matches") if m.category in {MatchCategory.IDENTIFIER_REVIEW, MatchCategory.SEMANTIC_OR_VISUAL_REVIEW})
    workflow.resolve_match(review_match.id, "Partner inspected package: recalled lot code not present")
    for task in repo.list("tasks"):
        workflow.acknowledge_task(task.id, "Demo partner lead", "Inventory isolated and counted")
    closed = repo.get("incidents", incident.id)

    exact = repo.get("inventory", "item_exact")
    review = repo.get("inventory", "item_review")
    control = repo.get("inventory", "item_control")
    assertions = {
        "incident_created": created,
        "duplicate_suppressed": not duplicate_created and duplicate.id == incident.id,
        "exact_item_quarantined": exact.status == InventoryStatus.QUARANTINED,
        "ambiguous_item_routed_to_review": review.status == InventoryStatus.HUMAN_REVIEW,
        "control_item_unchanged": control.status == InventoryStatus.AVAILABLE,
        "internal_closed_after_human_actions": str(closed.state) == "INTERNAL_CLOSED",
        "audit_events_recorded": len(repo.list("audit_events")) >= 8,
    }
    if not all(assertions.values()):
        raise SystemExit(json.dumps(assertions, indent=2))
    print(json.dumps({"status": "PASS", "incident_id": incident.id, "assertions": assertions}, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
