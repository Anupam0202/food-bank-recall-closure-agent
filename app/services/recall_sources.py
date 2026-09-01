from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from app.domain.models import RecallSource

OPENFDA_LIMITATION = (
    "openFDA data is unvalidated and is not used here to issue public alerts or track the official "
    "recall lifecycle. This prototype coordinates an internal operational response only."
)


def stable_hash(payload: dict[str, Any] | str) -> str:
    raw = json.dumps(payload, sort_keys=True, ensure_ascii=False) if isinstance(payload, dict) else payload
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def source_from_payload(payload: dict[str, Any] | str, provider: str, source_url: str, limitations: str) -> RecallSource:
    digest = stable_hash(payload)
    source_id = hashlib.sha256(f"{provider}|{digest}".encode()).hexdigest()[:20]
    return RecallSource(
        id=f"source_{source_id}",
        provider=provider,
        source_url=source_url,
        source_hash=digest,
        raw_payload=payload,
        limitations=limitations,
    )


def load_fixture(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def fetch_openfda_by_recall_number(recall_number: str, timeout: float = 10.0) -> dict[str, Any]:
    """Operator-initiated import; never an autonomous public alert feed."""
    import urllib.parse
    import urllib.request

    query = urllib.parse.urlencode({"search": f'recall_number:"{recall_number}"', "limit": 1})
    url = "https://api.fda.gov/food/enforcement.json?" + query
    request = urllib.request.Request(url, headers={"User-Agent": "food-bank-recall-closure-demo/1.0"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        payload = json.loads(response.read().decode("utf-8"))
    results = payload.get("results") or []
    if not results:
        raise LookupError("No matching openFDA record")
    return {"meta": payload.get("meta", {}), "record": results[0], "source_url": url}
