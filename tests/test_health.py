import importlib.util
import unittest

from app.config import Settings
from app.services.status_service import status_payload


class HealthPayloadTests(unittest.TestCase):
    def test_status_discloses_modes(self):
        payload = status_payload(Settings())
        self.assertEqual(payload["status"], "ok")
        self.assertEqual(payload["ai_mode"], "MOCK_GEMINI")
        self.assertEqual(payload["repository"], "IN_MEMORY")
        self.assertEqual(payload["media"], "LOCAL_MEDIA")


@unittest.skipUnless(importlib.util.find_spec("fastapi"), "FastAPI unavailable in offline sandbox")
class HealthEndpointTests(unittest.TestCase):
    def test_health_dashboard_and_readiness_contract(self):
        from fastapi.testclient import TestClient

        from app.main import app

        client = TestClient(app)
        health = client.get("/healthz")
        self.assertEqual(health.status_code, 200)
        self.assertEqual(health.json()["status"], "ok")

        dashboard = client.get("/")
        self.assertEqual(dashboard.status_code, 200)
        self.assertIn('data-app-id="food-bank-recall-closure-agent"', dashboard.text)
        self.assertIn("Turn a recall notice into verified internal action.", dashboard.text)

        readiness = client.get("/api/readiness")
        self.assertEqual(readiness.status_code, 200)
        self.assertIn("cloud_deployment", readiness.json())
        self.assertNotIn("gemini_api_key", readiness.text.lower())
