import base64
import json
import unittest

from app.domain.exceptions import ValidationError
from app.services.pubsub_service import decode_pubsub_envelope


def envelope(payload, message_id="m1", attempt=1):
    return {"message": {"messageId": message_id, "data": base64.b64encode(json.dumps(payload).encode()).decode()}, "deliveryAttempt": attempt}


class PubSubServiceTests(unittest.TestCase):
    def test_valid_envelope(self):
        result = decode_pubsub_envelope(envelope({"record": {"recall_number": "R"}}, attempt=2), 1000)
        self.assertEqual(result.message_id, "m1")
        self.assertEqual(result.delivery_attempt, 2)
        self.assertEqual(len(result.payload_hash), 64)

    def test_malformed_envelope(self):
        with self.assertRaises(ValidationError):
            decode_pubsub_envelope({}, 100)

    def test_invalid_base64(self):
        with self.assertRaises(ValidationError):
            decode_pubsub_envelope({"message": {"data": "%%%"}}, 100)

    def test_oversized_payload(self):
        with self.assertRaises(ValidationError):
            decode_pubsub_envelope(envelope({"value": "x" * 100}), 10)

    def test_json_array_is_poison(self):
        encoded = base64.b64encode(b"[]").decode()
        with self.assertRaises(ValidationError):
            decode_pubsub_envelope({"message": {"data": encoded}}, 100)
