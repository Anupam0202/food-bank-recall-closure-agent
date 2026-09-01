import unittest

from app.agents.coordinator import AdkCoordinator
from app.domain.enums import IncidentState, InventoryStatus, MatchCategory
from app.domain.exceptions import UnsafeActionError
from app.domain.models import Agency, InventoryItem
from app.repositories.memory import InMemoryRepository
from app.services.demo_data import seed_demo
from app.services.gemini_service import GeminiService
from app.workflows.recall_workflow import RecallWorkflow


class GoldenPathTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.repo = InMemoryRepository()
        self.gemini = GeminiService("mock", "gemini-3.7-flash")
        self.workflow = RecallWorkflow(self.repo, AdkCoordinator("mock", "gemini-3.7-flash"), "gemini-3.7-flash")
        self.source, self.recall = seed_demo(self.repo, self.gemini)

    async def test_golden_path_and_duplicate_event(self):
        incident, created = await self.workflow.process(self.source, self.recall)
        self.assertTrue(created)
        self.assertEqual(incident.state, IncidentState.AWAITING_ACK)
        self.assertEqual(self.repo.get("inventory", "item_exact").status, InventoryStatus.QUARANTINED)
        self.assertEqual(self.repo.get("inventory", "item_review").status, InventoryStatus.HUMAN_REVIEW)
        self.assertEqual(self.repo.get("inventory", "item_control").status, InventoryStatus.AVAILABLE)
        self.assertEqual(len(self.repo.list("tasks")), 2)

        same, duplicate_created = await self.workflow.process(self.source, self.recall)
        self.assertFalse(duplicate_created)
        self.assertEqual(same.id, incident.id)
        self.assertEqual(len(self.repo.list("tasks")), 2)

    async def test_human_actions_required_before_internal_closure(self):
        incident, _ = await self.workflow.process(self.source, self.recall)
        review = next(m for m in self.repo.list("matches") if m.category in {MatchCategory.IDENTIFIER_REVIEW, MatchCategory.SEMANTIC_OR_VISUAL_REVIEW})
        self.workflow.resolve_match(review.id, "Inspected: recalled lot is not present")
        for task in self.repo.list("tasks"):
            self.workflow.acknowledge_task(task.id, "Partner lead", "Stock checked")
        closed = self.repo.get("incidents", incident.id)
        self.assertEqual(closed.state, IncidentState.INTERNAL_CLOSED)
        internal_closure_events = [e for e in self.repo.list("audit_events") if e.event_type == "INTERNAL_CLOSED"]
        self.assertEqual(len(internal_closure_events), 1)

    async def test_disposal_cannot_be_authorized(self):
        await self.workflow.process(self.source, self.recall)
        match = next(m for m in self.repo.list("matches") if m.category == MatchCategory.EXACT_MATCH)
        with self.assertRaises(UnsafeActionError):
            self.workflow.resolve_match(match.id, "dispose")

    async def test_resolution_after_acknowledgements_closes_incident(self):
        incident, _ = await self.workflow.process(self.source, self.recall)
        for task in self.repo.list("tasks"):
            self.workflow.acknowledge_task(task.id, "Partner lead", "Count complete")
        self.assertEqual(self.repo.get("incidents", incident.id).state, IncidentState.AWAITING_ACK)
        review = next(m for m in self.repo.list("matches") if m.category != MatchCategory.EXACT_MATCH and m.category != MatchCategory.NO_MATCH)
        self.workflow.resolve_match(review.id, "Inspected: recalled lot is not present")
        self.assertEqual(self.repo.get("incidents", incident.id).state, IncidentState.INTERNAL_CLOSED)

    async def test_no_match_still_requires_human_confirmation(self):
        repo = InMemoryRepository()
        repo.put("agencies", "a", Agency("a", "Control Pantry", "District", "Coordinator"))
        repo.put("inventory", "control", InventoryItem("control", "a", "Rice crackers", "Meadow", "999999111112", "MP0512", None, 3))
        workflow = RecallWorkflow(repo, AdkCoordinator("mock", "gemini-3.7-flash"), "gemini-3.7-flash")
        incident, _ = await workflow.process(self.source, self.recall)
        self.assertEqual(incident.state, IncidentState.AWAITING_ACK)
        tasks = repo.list("tasks")
        self.assertEqual(len(tasks), 1)
        self.assertEqual(tasks[0].agency_id, "coordinator")
        workflow.acknowledge_task(tasks[0].id, "Recall coordinator", "No distributed stock affected")
        self.assertEqual(repo.get("incidents", incident.id).state, IncidentState.INTERNAL_CLOSED)

    async def test_human_confirmed_affected_review_becomes_quarantine(self):
        await self.workflow.process(self.source, self.recall)
        review = next(m for m in self.repo.list("matches") if m.category == MatchCategory.IDENTIFIER_REVIEW)
        self.workflow.resolve_match(review.id, "Confirmed affected: recalled lot present")
        self.assertEqual(self.repo.get("inventory", "item_review").status, InventoryStatus.QUARANTINED)
