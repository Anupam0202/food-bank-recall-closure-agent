import importlib.util
import json
import os
import unittest
from pathlib import Path


@unittest.skipUnless(os.getenv("RUN_LIVE_GEMINI_TESTS") == "1" and importlib.util.find_spec("google.genai"), "Set RUN_LIVE_GEMINI_TESTS=1 with credentials")
class LiveGeminiIntegrationTests(unittest.TestCase):
    def test_live_fixture_extraction(self):
        from app.services.gemini_service import GeminiService
        root = Path(__file__).parents[1]
        payload = json.loads((root / "fixtures/recalls/synthetic_recall.json").read_text())
        result = GeminiService("live", os.getenv("MODEL_NAME", "gemini-3.7-flash"), os.environ["GEMINI_API_KEY"]).extract_recall(payload)
        self.assertTrue(result.recall_number)
