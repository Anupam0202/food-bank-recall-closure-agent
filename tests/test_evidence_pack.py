import json
import unittest
from io import BytesIO
from zipfile import ZipFile

from app.domain.enums import ConfidenceCategory, IncidentState, InventoryStatus, MatchCategory, TaskStatus
from app.domain.models import AuditEvent, Incident, InventoryItem, MatchDecision, PartnerTask, Recall, RecallSource
from app.repositories.memory import InMemoryRepository
from app.services.evidence_pack_service import build_evidence_pack, verify_evidence_pack


class EvidencePackTests(unittest.TestCase):
    def setUp(self):
        self.repo = InMemoryRepository()
        source = RecallSource("source_1", "SYNTHETIC", "fixture://recall", "a" * 64, {"private": "raw bytes"}, "Synthetic")
        recall = Recall("recall_1", "R-1", "E-1", "Class I", "Oat bites", ["Harvest"], ["123"], ["LOT1"], [], "Reason", "US", "Firm", source.id)
        incident = Incident("incident_1", "key", recall.id, state=IncidentState.INTERNAL_CLOSED, exact_match_count=1, affected_agency_count=1)
        item = InventoryItem("item_1", "agency_1", "Oat bites", "Harvest", "123", "LOT1", None, 4, status=InventoryStatus.QUARANTINED)
        match = MatchDecision("match_1", incident.id, item.id, MatchCategory.EXACT_MATCH, ["upc", "lot_code"], ConfidenceCategory.SOURCE_EXACT, ["Exact identifiers"])
        task = PartnerTask("task_1", incident.id, "agency_1", [item.id], "Acknowledge hold", status=TaskStatus.ACKNOWLEDGED, acknowledged_by="Lead")
        events = [
            AuditEvent("audit_1", incident.id, incident.correlation_id, "SYSTEM", "INCIDENT_RECEIVED", "Received", created_at="2026-01-01T00:00:00+00:00"),
            AuditEvent("audit_2", incident.id, incident.correlation_id, "SYSTEM", "INTERNAL_CLOSED", "Closed internally", created_at="2026-01-01T00:01:00+00:00"),
        ]
        for collection, value in [("recall_sources", source), ("recalls", recall), ("incidents", incident), ("inventory", item), ("matches", match), ("tasks", task)]:
            self.repo.put(collection, value.id, value)
        for event in events:
            self.repo.put("audit_events", event.id, event)

    def test_pack_hashes_and_audit_chain_verify(self):
        payload, manifest = build_evidence_pack(self.repo, "incident_1", "2026-01-01T01:00:00+00:00")
        result = verify_evidence_pack(payload)
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(manifest["finality"], "FINAL_INTERNAL_CLOSURE")
        self.assertTrue(manifest["authenticity"].startswith("UNSIGNED"))
        self.assertEqual(result["files_verified"], 10)

    def test_pack_excludes_raw_source_and_secret_material(self):
        payload, _ = build_evidence_pack(self.repo, "incident_1")
        with ZipFile(BytesIO(payload)) as archive:
            provenance = json.loads(archive.read("source-provenance.json"))
            self.assertNotIn("raw_payload", provenance)
            self.assertFalse(provenance["raw_payload_included"])
            self.assertNotIn(b"raw bytes", payload)
            self.assertNotIn("manifest.json", json.loads(archive.read("manifest.json"))["privacy"])

    def test_open_incident_pack_is_provisional(self):
        incident = self.repo.get("incidents", "incident_1")
        incident.state = IncidentState.AWAITING_ACK
        self.repo.put("incidents", incident.id, incident)
        _, manifest = build_evidence_pack(self.repo, incident.id)
        self.assertEqual(manifest["finality"], "PROVISIONAL_OPEN_INCIDENT")

    def test_missing_incident_fails_closed(self):
        with self.assertRaises(LookupError):
            build_evidence_pack(self.repo, "missing")
