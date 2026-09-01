import os
import unittest
from unittest.mock import patch

from app.config import Settings


class SettingsTests(unittest.TestCase):
    def test_environment_is_resolved_for_each_new_instance(self):
        with patch.dict(os.environ, {"PORT": "9099", "AI_MODE": "replay", "CLOUD_RUN_MAX_INSTANCES": "2"}, clear=False):
            current = Settings()
        self.assertEqual(current.port, 9099)
        self.assertEqual(current.ai_mode, "replay")
        self.assertEqual(current.cloud_run_max_instances, 2)

    def test_production_rejects_insecure_defaults(self):
        with self.assertRaises(ValueError):
            Settings(app_env="production").validate()

    def test_production_accepts_required_controls(self):
        configured = Settings(
            app_env="production",
            app_base_url="https://service.example",
            session_secret="x" * 32,
            demo_admin_token="private-token",
            ai_mode="live",
            gemini_api_key="x" * 32,
            use_firestore=True,
            google_cloud_project="demo-project",
            use_cloud_storage=True,
            gcs_bucket="private-evidence-bucket",
            pubsub_verification_audience="https://service.example",
        )
        configured.validate()

    def test_production_rejects_non_https_audience(self):
        configured = Settings(
            app_env="production", app_base_url="https://service.example",
            session_secret="x" * 32, demo_admin_token="private-token",
            ai_mode="live", gemini_api_key="x" * 32, use_firestore=True,
            google_cloud_project="demo-project", use_cloud_storage=True,
            gcs_bucket="private-evidence-bucket", pubsub_verification_audience="http://service.example",
        )
        with self.assertRaises(ValueError):
            configured.validate()

    def test_invalid_mode_is_rejected(self):
        with self.assertRaises(ValueError):
            Settings(ai_mode="unknown").validate()
