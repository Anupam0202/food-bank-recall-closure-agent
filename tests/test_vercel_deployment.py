import json
import os
import tomllib
import unittest
from pathlib import Path
from unittest.mock import patch

from app.config import Settings
from app.services.readiness_service import readiness_payload

ROOT = Path(__file__).resolve().parents[1]


class VercelDeploymentTests(unittest.TestCase):
    def test_vercel_source_contract(self):
        config = json.loads((ROOT / "vercel.json").read_text())
        function = config["functions"]["app/main.py"]
        self.assertLessEqual(function["maxDuration"], 300)
        project = tomllib.loads((ROOT / "pyproject.toml").read_text())
        self.assertEqual(project["tool"]["vercel"]["entrypoint"], "app.main:app")
        self.assertEqual((ROOT / ".python-version").read_text().strip(), "3.12")

    def test_vercel_environment_defaults_fail_closed_without_secrets(self):
        with patch.dict(os.environ, {"VERCEL": "1", "VERCEL_URL": "preview.vercel.app"}, clear=True):
            settings = Settings()
        self.assertEqual(settings.app_env, "demo")
        self.assertEqual(settings.deployment_target, "vercel")
        self.assertEqual(settings.runtime_upload_dir, "/tmp/recall-closure/uploads")
        with self.assertRaises(ValueError):
            settings.validate()

    def test_secure_vercel_demo_profile_is_valid(self):
        settings = Settings(
            app_env="demo", deployment_target="vercel",
            app_base_url="https://preview.vercel.app",
            session_secret="s" * 40, demo_admin_token="a" * 24,
            max_document_bytes=4_000_000, max_image_bytes=4_000_000,
            runtime_upload_dir="/tmp/recall-closure/uploads",
        )
        settings.validate()
        payload = readiness_payload(settings)
        self.assertTrue(payload["hosted_preview"]["ready"])
        self.assertFalse(payload["cloud_deployment"]["ready"])
        self.assertIn("ephemeral", payload["hosted_preview"]["durability_warning"].lower())

    def test_vercel_payload_over_platform_limit_is_rejected(self):
        settings = Settings(
            app_env="demo", deployment_target="vercel",
            app_base_url="https://preview.vercel.app",
            session_secret="s" * 40, demo_admin_token="a" * 24,
            max_document_bytes=4_000_001, max_image_bytes=4_000_000,
        )
        with self.assertRaises(ValueError):
            settings.validate()

    def test_hosted_demo_requires_https(self):
        settings = Settings(
            app_env="demo", deployment_target="vercel",
            app_base_url="http://preview.example",
            session_secret="s" * 40, demo_admin_token="a" * 24,
            max_document_bytes=4_000_000, max_image_bytes=4_000_000,
        )
        with self.assertRaises(ValueError):
            settings.validate()

    def test_vercel_ignore_excludes_secrets_and_build_artifacts(self):
        ignored = set((ROOT / ".vercelignore").read_text().splitlines())
        self.assertTrue({".env", ".git", ".venv", "runtime", "*.zip"}.issubset(ignored))
