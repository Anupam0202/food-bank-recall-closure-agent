from __future__ import annotations

import hashlib

from app.domain.models import Recall, RecallSource


def incident_key(source: RecallSource, recall: Recall) -> str:
    raw = f"{source.provider}|{recall.recall_number}|{source.source_hash}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def stable_id(prefix: str, *parts: str) -> str:
    digest = hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()[:16]
    return f"{prefix}_{digest}"
