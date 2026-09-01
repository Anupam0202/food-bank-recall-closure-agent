import unittest

from app.domain.models import Recall, RecallSource
from app.services.recall_sources import source_from_payload
from app.workflows.idempotency import incident_key, stable_id


class IdempotencyTests(unittest.TestCase):
    def setUp(self):
        self.source = RecallSource("s", "P", "u", "hash", {}, "limit")
        self.recall = Recall("r", "N", "E", "C", "Product", [], [], [], [], "reason", "dist", "firm", "s")

    def test_incident_key_is_stable(self):
        self.assertEqual(incident_key(self.source, self.recall), incident_key(self.source, self.recall))

    def test_provider_number_or_hash_changes_key(self):
        first = incident_key(self.source, self.recall)
        self.source.source_hash = "different"
        self.assertNotEqual(first, incident_key(self.source, self.recall))

    def test_stable_child_ids(self):
        self.assertEqual(stable_id("task", "incident", "agency"), stable_id("task", "incident", "agency"))
        self.assertNotEqual(stable_id("task", "incident", "a"), stable_id("task", "incident", "b"))

    def test_duplicate_payload_has_stable_source_id(self):
        first = source_from_payload({"recall_number": "R"}, "P", "u1", "limit")
        second = source_from_payload({"recall_number": "R"}, "P", "u2", "limit")
        self.assertEqual(first.id, second.id)
        self.assertEqual(first.source_hash, second.source_hash)
