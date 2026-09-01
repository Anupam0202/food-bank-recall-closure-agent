import unittest

from app.repositories.memory import InMemoryRepository
from app.services.task_service import TaskService


class TaskServiceTests(unittest.TestCase):
    def test_task_creation_is_idempotent(self):
        service = TaskService(InMemoryRepository())
        first = service.create_partner_task("i", "a", ["x"], "review")
        second = service.create_partner_task("i", "a", ["x"], "review")
        self.assertEqual(first.id, second.id)

    def test_acknowledgement_is_idempotent(self):
        service = TaskService(InMemoryRepository())
        task = service.create_partner_task("i", "a", [], "confirm")
        _, changed = service.acknowledge(task.id, "Actor", "Done")
        _, changed_again = service.acknowledge(task.id, "Other", "Again")
        self.assertTrue(changed)
        self.assertFalse(changed_again)

    def test_evidence_is_attached(self):
        service = TaskService(InMemoryRepository())
        task = service.create_partner_task("i", "a", [], "confirm")
        updated = service.attach_evidence(task.id, "gs://private/object")
        self.assertEqual(updated.evidence_uri, "gs://private/object")
