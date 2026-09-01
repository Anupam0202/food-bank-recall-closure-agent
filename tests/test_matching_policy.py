import unittest

from app.domain.enums import MatchCategory
from app.domain.matching_policy import decide_match, normalize_lot, normalize_upc
from app.domain.models import InventoryItem, Recall


def recall():
    return Recall("r1", "R-1", "E-1", "Class II", "Harvest Table Oat Bites 12 oz", ["Harvest Table"], ["012345678905"], ["HT2409A"], [], "reason", "region", "firm", "s1")


def item(upc="0-12345-67890-5", lot="HT-2409-A", name="Harvest Table Oat Bites 12 oz", brand="Harvest Table"):
    return InventoryItem("i1", "a1", name, brand, upc, lot, None, 1)


class MatchingPolicyTests(unittest.TestCase):
    def test_normalizers(self):
        self.assertEqual(normalize_upc("0-12345 67890-5"), "012345678905")
        self.assertEqual(normalize_lot("ht-2409 a"), "HT2409A")

    def test_exact_match_requires_upc_and_lot(self):
        result = decide_match(recall(), item())
        self.assertEqual(result.category, MatchCategory.EXACT_MATCH)
        self.assertTrue(result.auto_quarantine)

    def test_partial_identifier_is_review(self):
        result = decide_match(recall(), item(lot=None))
        self.assertEqual(result.category, MatchCategory.IDENTIFIER_REVIEW)
        self.assertFalse(result.auto_quarantine)

    def test_text_only_overlap_is_review_not_hold(self):
        result = decide_match(recall(), item(upc="777777777777", lot="OTHER"))
        self.assertEqual(result.category, MatchCategory.SEMANTIC_OR_VISUAL_REVIEW)
        self.assertFalse(result.auto_quarantine)

    def test_unrelated_item_is_no_match(self):
        result = decide_match(recall(), item(upc="999999111112", lot="MP0512", name="Rice crackers", brand="Meadow"))
        self.assertEqual(result.category, MatchCategory.NO_MATCH)
