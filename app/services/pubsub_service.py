from __future__ import annotations

import base64
import binascii
import hashlib
import json
from dataclasses import dataclass
from typing import Any

from app.domain.exceptions import ValidationError


@dataclass(frozen=True)
class DecodedPubSubMessage:
    message_id: str
    payload: dict[str, Any]
    payload_hash: str
    delivery_attempt: int


def decode_pubsub_envelope(envelope: Any, max_bytes: int) -> DecodedPubSubMessage:
    if not isinstance(envelope, dict) or not isinstance(envelope.get("message"), dict):
        raise ValidationError("Malformed Pub/Sub envelope")
    message = envelope["message"]
    encoded = message.get("data")
    if not isinstance(encoded, str) or not encoded:
        raise ValidationError("Pub/Sub message data is required")
    try:
        raw = base64.b64decode(encoded, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise ValidationError("Pub/Sub data is not valid Base64") from exc
    if len(raw) > max_bytes:
        raise ValidationError("Pub/Sub payload exceeds the configured limit")
    try:
        payload = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValidationError("Pub/Sub data must be a UTF-8 JSON object") from exc
    if not isinstance(payload, dict):
        raise ValidationError("Pub/Sub payload must be an object")
    attempt = envelope.get("deliveryAttempt", 1)
    return DecodedPubSubMessage(
        message_id=str(message.get("messageId") or message.get("message_id") or "unknown"),
        payload=payload,
        payload_hash=hashlib.sha256(raw).hexdigest(),
        delivery_attempt=int(attempt) if str(attempt).isdigit() else 1,
    )
