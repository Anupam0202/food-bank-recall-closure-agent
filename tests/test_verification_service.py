import unittest

from app.domain.enums import ConfidenceCategory, InventoryStatus, MatchCategory, TaskStatus
from app.domain.models import InventoryItem, MatchDecision, PartnerTask
from app.services.verification_service import VerificationService


class VerificationServiceTests(unittest.TestCase):
    def test_exact_item_must_be_held(self):
        item = InventoryItem("item", "a", "P", "B", "1", "L", None, 1)
        match = MatchDecision("m", "i", "item", MatchCategory.EXACT_MATCH, ["upc", "lot"], ConfidenceCategory.SOURCE_EXACT, [])
        task = PartnerTask("t", "i", "a", ["item"], "ack", status=TaskStatus.ACKNOWLEDGED)
        blockers = VerificationService.closure_blockers([match], [task], [item])
        self.assertTrue(any("not on quarantine" in blocker for blocker in blockers))
        item.status = InventoryStatus.QUARANTINED
        self.assertEqual(VerificationService.closure_blockers([match], [task], [item]), [])

    def test_failed_task_blocks(self):
        task = PartnerTask("t", "i", "a", [], "ack", status=TaskStatus.FAILED)
        blockers = VerificationService.closure_blockers([], [task], [])
        self.assertTrue(any("failed" in blocker for blocker in blockers))
