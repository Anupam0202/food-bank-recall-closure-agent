import unittest

from app.domain.enums import IncidentState, MatchCategory, TaskStatus
from app.domain.exceptions import InvalidTransition
from app.domain.models import Incident, MatchDecision, PartnerTask
from app.domain.state_machine import closure_blockers, transition


class StateMachineTests(unittest.TestCase):
    def test_happy_transition(self):
        incident = Incident("i", "key", "r")
        transition(incident, IncidentState.SOURCE_VALIDATED)
        self.assertEqual(incident.state, IncidentState.SOURCE_VALIDATED)

    def test_illegal_jump_rejected(self):
        incident = Incident("i", "key", "r")
        with self.assertRaises(InvalidTransition):
            transition(incident, IncidentState.INTERNAL_CLOSED)

    def test_review_and_ack_block_closure(self):
        match = MatchDecision("m", "i", "inv", MatchCategory.IDENTIFIER_REVIEW, ["upc"], "AMBIGUOUS", ["lot missing"])
        task = PartnerTask("t", "i", "a", ["inv"], "review")
        blockers = closure_blockers([match], [task])
        self.assertEqual(len(blockers), 2)
        match.human_resolution = "not affected"
        task.status = TaskStatus.ACKNOWLEDGED
        self.assertEqual(closure_blockers([match], [task]), [])
