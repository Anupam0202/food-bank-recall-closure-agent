import unittest

from app.config import Settings
from app.services.readiness_service import readiness_payload


class ReadinessTests(unittest.TestCase):
    def test_default_local_profile_is_ready_without_secret_disclosure(self):
        payload = readiness_payload(Settings())
        self.assertTrue(payload["local_demo"]["ready"])
        self.assertFalse(payload["cloud_deployment"]["ready"])
        serialized = str(payload).lower()
        self.assertNotIn("development-only-change-me", serialized)
        self.assertNotIn("demo-admin", serialized)

    def test_complete_cloud_profile_is_ready(self):
        settings = Settings(
            app_env="production",
            app_base_url="https://service.example",
            session_secret="s" * 40,
            demo_admin_token="a" * 24,
            ai_mode="live",
            gemini_api_key="k" * 32,
            google_cloud_project="demo-project",
            use_firestore=True,
            gcs_bucket="private-bucket",
            use_cloud_storage=True,
            pubsub_verification_audience="https://service.example",
        )
        payload = readiness_payload(settings)
        self.assertTrue(payload["cloud_deployment"]["ready"])
        self.assertEqual(payload["cloud_deployment"]["score"], 100)
        self.assertEqual(payload["cost_guardrails"]["max_instances"], 1)

    def test_non_free_storage_region_is_disclosed(self):
        payload = readiness_payload(Settings(google_cloud_region="asia-south1"))
        self.assertFalse(payload["cost_guardrails"]["region_optimized_for_storage_free_tier"])
