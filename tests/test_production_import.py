import importlib.util
import unittest


def available(name):
    try:
        return importlib.util.find_spec(name) is not None
    except (ImportError, ModuleNotFoundError):
        return False


@unittest.skipUnless(available("fastapi") and available("google.adk"), "Production dependencies unavailable")
class ProductionImportTests(unittest.TestCase):
    def test_fastapi_and_adk_entrypoints_import(self):
        import agent
        import app.main
        self.assertIsNotNone(app.main.app)
        self.assertIsNotNone(agent.root_agent)
