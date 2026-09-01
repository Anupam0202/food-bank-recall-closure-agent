import unittest

from app.domain.enums import ConfidenceCategory, IncidentState, InventoryStatus, MatchCategory, TaskStatus
from app.domain.models import Incident, InventoryItem, MatchDecision, PartnerTask
from app.repositories.firestore import FirestoreRepository


class FirestoreHydrationTests(unittest.TestCase):
    def test_inventory_hydrates_status_enum(self):
        payload = InventoryItem("item", "agency", "Product", "Brand", "123", "LOT", None, 1).to_dict()
        payload["status"] = "QUARANTINED"
        item = FirestoreRepository._hydrate("inventory", payload)
        self.assertEqual(item.status, InventoryStatus.QUARANTINED)

    def test_incident_match_and_task_hydrate_enums(self):
        incident_payload = Incident("incident", "key", "recall").to_dict()
        incident_payload["state"] = "AWAITING_ACK"
        incident = FirestoreRepository._hydrate("incidents", incident_payload)
        self.assertEqual(incident.state, IncidentState.AWAITING_ACK)

        match_payload = MatchDecision(
            "match", "incident", "item", MatchCategory.IDENTIFIER_REVIEW,
            ["upc"], ConfidenceCategory.AMBIGUOUS, ["lot missing"],
        ).to_dict()
        match = FirestoreRepository._hydrate("matches", match_payload)
        self.assertEqual(match.category, MatchCategory.IDENTIFIER_REVIEW)
        self.assertEqual(match.confidence_category, ConfidenceCategory.AMBIGUOUS)

        task_payload = PartnerTask("task", "incident", "agency", [], "Confirm").to_dict()
        task_payload["status"] = "ACKNOWLEDGED"
        task = FirestoreRepository._hydrate("tasks", task_payload)
        self.assertEqual(task.status, TaskStatus.ACKNOWLEDGED)
