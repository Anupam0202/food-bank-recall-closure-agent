import unittest

from app.domain.enums import IncidentState
from app.domain.exceptions import InvalidTransition
from app.domain.models import Incident
from app.repositories.memory import InMemoryRepository
from app.services.audit_service import AuditService


class AuditTransitionTests(unittest.TestCase):
    def test_successful_transition_is_audited(self):
        repo = InMemoryRepository()
        incident = Incident("i", "k", "r")
        repo.put("incidents", incident.id, incident)
        AuditService(repo).transition(incident, IncidentState.SOURCE_VALIDATED)
        self.assertEqual(repo.list("audit_events")[0].event_type, "STATE_TRANSITION")

    def test_rejected_transition_is_audited(self):
        repo = InMemoryRepository()
        incident = Incident("i", "k", "r")
        repo.put("incidents", incident.id, incident)
        with self.assertRaises(InvalidTransition):
            AuditService(repo).transition(incident, IncidentState.INTERNAL_CLOSED)
        events = repo.list("audit_events")
        self.assertEqual(events[0].event_type, "STATE_TRANSITION_REJECTED")
