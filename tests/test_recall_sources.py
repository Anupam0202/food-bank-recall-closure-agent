import json
import unittest
from unittest.mock import patch

from app.services.recall_sources import fetch_openfda_by_recall_number


class _Response:
    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self):
        return json.dumps({"results": [{"recall_number": "F-1234-2026"}]}).encode()


class RecallSourceTests(unittest.TestCase):
    def test_openfda_url_is_valid_and_encoded(self):
        captured = {}

        def fake_urlopen(request, timeout):
            captured["url"] = request.full_url
            return _Response()

        with patch("urllib.request.urlopen", fake_urlopen):
            result = fetch_openfda_by_recall_number("F-1234-2026")
        self.assertTrue(captured["url"].startswith("https://api.fda.gov/food/enforcement.json?"))
        self.assertNotIn("{https", captured["url"])
        self.assertEqual(result["record"]["recall_number"], "F-1234-2026")
