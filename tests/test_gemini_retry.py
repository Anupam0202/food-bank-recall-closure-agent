import unittest
from unittest.mock import Mock

from app.agents.output_schemas import RecallExtraction
from app.domain.exceptions import ModelSchemaError
from app.services.gemini_service import GeminiService


class GeminiRetryTests(unittest.TestCase):
    def result(self):
        return RecallExtraction(recall_number="R", product_description="Product", reason="Reason")

    def test_transient_failures_use_bounded_retry(self):
        sleeps = []
        service = GeminiService("live", "gemini-3.7-flash", "test-key", 3, sleeps.append)
        call = Mock(side_effect=[TimeoutError(), TimeoutError(), self.result()])
        service._live_extract_once = call
        output = service.extract_recall("text")
        self.assertEqual(output.recall_number, "R")
        self.assertEqual(call.call_count, 3)
        self.assertEqual(len(sleeps), 2)
        self.assertEqual(service.last_call.attempt_count, 3)

    def test_permanent_error_is_not_retried(self):
        service = GeminiService("live", "gemini-3.7-flash", "test-key", 3, lambda _: None)
        call = Mock(side_effect=ValueError("bad input"))
        service._live_extract_once = call
        with self.assertRaises(ValueError):
            service.extract_recall("text")
        self.assertEqual(call.call_count, 1)

    def test_schema_error_is_typed(self):
        response = type("Response", (), {"parsed": None, "text": "{}"})()
        with self.assertRaises(ModelSchemaError):
            GeminiService._parse_response(response)
