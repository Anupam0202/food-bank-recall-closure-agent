import importlib.util
import tempfile
import unittest
from pathlib import Path


class CloudToolContractTests(unittest.TestCase):
    def test_local_env_builder_generates_strong_secrets_without_cloud(self):
        path = Path(__file__).parents[1] / "scripts" / "configure_local_env.py"
        spec = importlib.util.spec_from_file_location("configure_local_env", path)
        module = importlib.util.module_from_spec(spec)
        assert spec.loader
        spec.loader.exec_module(module)
        env = module.values(False)
        self.assertEqual(env["AI_MODE"], "mock")
        self.assertEqual(env["USE_FIRESTORE"], "false")
        self.assertGreaterEqual(len(env["SESSION_SECRET"]), 32)
        self.assertGreaterEqual(len(env["DEMO_ADMIN_TOKEN"]), 12)
        self.assertNotIn("None", module.serialize(env))

    def test_cloud_collector_is_read_only_by_contract(self):
        source = (Path(__file__).parents[1] / "scripts" / "gcp_collect_config.py").read_text()
        self.assertIn("secret_values_exposed", source)
        self.assertNotIn("secrets versions access", source)
        self.assertNotIn("services enable", source)
