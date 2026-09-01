import unittest
from pathlib import Path


class RouteContractTests(unittest.TestCase):
    def test_required_routes_are_declared(self):
        root = Path(__file__).parents[1] / "app"
        source = "\n".join(path.read_text() for path in root.rglob("*.py"))
        required = [
            '"/healthz"', '"/api/system-status"', '"/"', '"/incidents/{incident_id}"',
            '"/inventory"', '"/partner/tasks"', '"/about"', '"/login"',
            '"/reset"', '"/seed"', '"/run-golden-path"', '"/recalls/upload"',
            '"/recalls/import"', '"/pubsub/recall"', '"/incidents/{incident_id}/retry"',
            '"/tasks/{task_id}/acknowledge"', '"/tasks/{task_id}/evidence"',
            '"/matches/{match_id}/resolve"', '"/incidents/{incident_id}/export.json"',
            '"/incidents/{incident_id}/print"', '"/media/{object_name}"',
            '"/incidents/{incident_id}/evidence-pack.zip"', '"/api/readiness"', '"/readiness"',
        ]
        for route in required:
            with self.subTest(route=route):
                self.assertIn(route, source)
