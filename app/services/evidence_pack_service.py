from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from io import BytesIO
from typing import Any
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

from app.domain.enums import IncidentState
from app.services.verification_service import VerificationService

ZERO_HASH = "0" * 64
SENSITIVE_KEYS = {"raw_payload", "gemini_api_key", "session_secret", "demo_admin_token", "authorization", "access_token", "refresh_token", "private_key", "secret"}


def _sanitize(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _sanitize(item) for key, item in value.items() if str(key).lower() not in SENSITIVE_KEYS}
    if isinstance(value, list):
        return [_sanitize(item) for item in value]
    if isinstance(value, tuple):
        return [_sanitize(item) for item in value]
    return value


def _canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def _pretty(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, indent=2, ensure_ascii=False) + "\n").encode("utf-8")


def _digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _records(values: list[Any]) -> list[dict[str, Any]]:
    records = [_sanitize(value.to_dict() if hasattr(value, "to_dict") else dict(value)) for value in values]
    return sorted(records, key=lambda item: (str(item.get("created_at", "")), str(item.get("id", ""))))


def _audit_chain(events: list[dict[str, Any]]) -> dict[str, Any]:
    previous = ZERO_HASH
    entries: list[dict[str, Any]] = []
    for index, event in enumerate(events, start=1):
        event_hash = _digest(_canonical(event))
        chain_hash = _digest(f"{previous}:{event_hash}".encode("ascii"))
        entries.append(
            {
                "sequence": index,
                "event_id": event.get("id"),
                "event_type": event.get("event_type"),
                "created_at": event.get("created_at"),
                "event_sha256": event_hash,
                "previous_chain_sha256": previous,
                "chain_sha256": chain_hash,
            }
        )
        previous = chain_hash
    return {
        "algorithm": "SHA-256",
        "genesis_sha256": ZERO_HASH,
        "event_count": len(entries),
        "entries": entries,
        "root_chain_sha256": previous,
    }


def _zip_write(archive: ZipFile, name: str, data: bytes) -> None:
    info = ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
    info.compress_type = ZIP_DEFLATED
    info.external_attr = 0o644 << 16
    archive.writestr(info, data)


def build_evidence_pack(repo: Any, incident_id: str, generated_at: str | None = None) -> tuple[bytes, dict[str, Any]]:
    """Build a privacy-minimized, tamper-evident operational closure packet."""

    incident = repo.get("incidents", incident_id)
    if not incident:
        raise LookupError("Incident not found")
    recall = repo.get("recalls", incident.recall_id)
    source = repo.get("recall_sources", recall.source_id) if recall else None
    matches = [item for item in repo.list("matches") if item.incident_id == incident_id]
    tasks = [item for item in repo.list("tasks") if item.incident_id == incident_id]
    audit = [item for item in repo.list("audit_events") if item.incident_id == incident_id]
    inventory_by_id = {item.id: item for item in repo.list("inventory")}
    selected_inventory = [inventory_by_id[item.inventory_item_id] for item in matches if item.inventory_item_id in inventory_by_id]
    blockers = VerificationService.closure_blockers(matches, tasks, list(inventory_by_id.values()))

    source_record = _sanitize(source.to_dict()) if source else None
    if source_record:
        source_record.pop("raw_payload", None)
        source_record["raw_payload_included"] = False
        source_record["privacy_note"] = "Original bytes remain in the configured private media store and are excluded from this portable pack."

    event_records = _records(audit)
    chain = _audit_chain(event_records)
    created = generated_at or datetime.now(UTC).isoformat()
    finality = "FINAL_INTERNAL_CLOSURE" if incident.state == IncidentState.INTERNAL_CLOSED else "PROVISIONAL_OPEN_INCIDENT"
    closure = {
        "incident_id": incident.id,
        "internal_state": str(incident.state),
        "finality": finality,
        "official_recall_status_changed": False,
        "closure_blockers": blockers,
        "exact_match_count": incident.exact_match_count,
        "review_count": incident.review_count,
        "affected_agency_count": incident.affected_agency_count,
        "audit_root_chain_sha256": chain["root_chain_sha256"],
    }
    files: dict[str, bytes] = {
        "README.txt": (
            b"Recall Closure evidence pack\n\n"
            b"This packet proves an organization's internal operational response only. "
            b"It does not declare product safety, authorize disposal, or change regulator recall status.\n"
            b"Original uploads and task media are excluded; hashes and private-store references remain in the records.\n"
            b"The manifest is unsigned. Preserve or publish the reported root hash separately when authenticity must be proven.\n"
        ),
        "incident.json": _pretty(_sanitize(incident.to_dict())),
        "recall.json": _pretty(_sanitize(recall.to_dict()) if recall else None),
        "source-provenance.json": _pretty(source_record),
        "inventory-decisions.json": _pretty({"matches": _records(matches), "inventory": _records(selected_inventory)}),
        "partner-tasks.json": _pretty(_records(tasks)),
        "audit-events.json": _pretty(event_records),
        "chain-of-custody.json": _pretty(chain),
        "closure-summary.json": _pretty(closure),
    }
    file_records = [
        {"path": name, "bytes": len(data), "sha256": _digest(data)}
        for name, data in sorted(files.items())
    ]
    root_material = "\n".join(f"{item['sha256']}  {item['path']}" for item in file_records).encode("utf-8")
    manifest = {
        "schema": "org.recall-closure.evidence-pack",
        "schema_version": 1,
        "application_version": "1.3.0",
        "generated_at": created,
        "incident_id": incident.id,
        "finality": finality,
        "hash_algorithm": "SHA-256",
        "authenticity": "UNSIGNED_SELF_CONTAINED_INTEGRITY; compare a separately trusted root for authenticity",
        "pack_root_sha256": _digest(root_material),
        "audit_root_chain_sha256": chain["root_chain_sha256"],
        "files": file_records,
        "privacy": {"raw_source_payload_included": False, "task_media_included": False, "secrets_included": False},
    }
    checksums = root_material + b"\n"
    files["SHA256SUMS.txt"] = checksums
    manifest["files"].append({"path": "SHA256SUMS.txt", "bytes": len(checksums), "sha256": _digest(checksums)})

    buffer = BytesIO()
    with ZipFile(buffer, "w") as archive:
        for name, data in sorted(files.items()):
            _zip_write(archive, name, data)
        _zip_write(archive, "manifest.json", _pretty(manifest))
    return buffer.getvalue(), manifest


def verify_evidence_pack(payload: bytes) -> dict[str, Any]:
    """Verify listed members, content digests, checksum root, and audit chain."""

    with ZipFile(BytesIO(payload)) as archive:
        if archive.testzip() is not None:
            raise ValueError("Evidence pack contains a corrupt member")
        manifest = json.loads(archive.read("manifest.json"))
        for record in manifest["files"]:
            data = archive.read(record["path"])
            if len(data) != record["bytes"] or _digest(data) != record["sha256"]:
                raise ValueError(f"Evidence member failed verification: {record['path']}")
        listed_without_checksums = [item for item in manifest["files"] if item["path"] != "SHA256SUMS.txt"]
        root_material = "\n".join(f"{item['sha256']}  {item['path']}" for item in listed_without_checksums).encode("utf-8")
        if _digest(root_material) != manifest["pack_root_sha256"]:
            raise ValueError("Evidence pack root digest does not match")
        chain = json.loads(archive.read("chain-of-custody.json"))
        previous = chain["genesis_sha256"]
        for entry in chain["entries"]:
            if entry["previous_chain_sha256"] != previous:
                raise ValueError("Audit chain linkage failed")
            expected = _digest(f"{previous}:{entry['event_sha256']}".encode("ascii"))
            if expected != entry["chain_sha256"]:
                raise ValueError("Audit chain digest failed")
            previous = expected
        if previous != chain["root_chain_sha256"] or previous != manifest["audit_root_chain_sha256"]:
            raise ValueError("Audit chain root does not match")
    return {"status": "PASS", "incident_id": manifest["incident_id"], "finality": manifest["finality"], "files_verified": len(manifest["files"]), "pack_root_sha256": manifest["pack_root_sha256"], "audit_root_chain_sha256": manifest["audit_root_chain_sha256"]}
