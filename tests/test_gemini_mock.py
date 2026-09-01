import json
import unittest
from pathlib import Path

from app.services.gemini_service import GeminiService


class GeminiMockTests(unittest.TestCase):
    def test_fixture_parses_to_schema(self):
        payload = json.loads((Path(__file__).parents[1] / "fixtures/recalls/synthetic_recall.json").read_text())
        result = GeminiService("mock", "gemini-3.7-flash").extract_recall(payload)
        self.assertEqual(result.recall_number, "SYNTHETIC-FB-2026-001")
        self.assertIn("012345678905", result.upc_candidates)

    def test_unstructured_text_has_deterministic_mock_fallback(self):
        text = "Recall number TEXT-2026-77. UPC 012345678905. Lot code HT-2409-A. Oat bites recall."
        result = GeminiService("mock", "gemini-3.7-flash").extract_recall(text)
        self.assertEqual(result.recall_number, "TEXT-2026-77")
        self.assertIn("012345678905", result.upc_candidates)
        self.assertIn("HT-2409-A", result.lot_codes)

    def test_mock_package_observation_is_review_only(self):
        result = GeminiService("mock", "gemini-3.7-flash").assess_package_bytes("Oat Bites", b"image", "image/png")
        self.assertEqual(result.confidence, "AMBIGUOUS")
