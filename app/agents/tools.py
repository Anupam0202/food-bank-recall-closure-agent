from __future__ import annotations

from typing import Any

SAFE_FIELDS = {
    "id", "state", "exact_match_count", "review_count", "affected_agency_count",
    "attempt_count", "recall_number", "classification", "product_description",
    "category", "inventory_item_id", "agency_id", "status", "required_action",
}


def _sanitize(value: dict[str, Any]) -> dict[str, Any]:
    return {key: value.get(key) for key in SAFE_FIELDS if key in value}


def load_recall_source(provider: str, source_url: str, source_hash: str, limitations: str) -> dict[str, str]:
    """Return source provenance only; never return a raw untrusted payload to the coordinator."""
    return {"provider": provider, "source_url": source_url, "source_hash": source_hash, "limitations": limitations}


def extract_recall_fields(extracted: dict[str, Any]) -> dict[str, Any]:
    """Return a sanitized view of already schema-validated recall extraction."""
    allowed = {"recall_number", "classification", "product_description", "brands", "upc_candidates", "lot_codes", "date_codes", "ambiguities", "confidence_category"}
    return {key: extracted.get(key) for key in allowed if key in extracted}


def query_inventory(items: list[dict[str, Any]], agency_id: str = "") -> dict[str, Any]:
    """Read sanitized inventory summaries, optionally scoped to one agency."""
    filtered = [item for item in items if not agency_id or item.get("agency_id") == agency_id]
    return {"count": len(filtered), "items": [_sanitize(item) for item in filtered[:100]], "truncated": len(filtered) > 100}


def evaluate_ambiguous_item(item: dict[str, Any], recall_identifiers: dict[str, Any]) -> dict[str, Any]:
    """Propose human review for ambiguous evidence; this tool can never create an exact match."""
    visible = [str(value) for value in item.get("visible_identifiers", [])]
    candidates = [str(value) for values in recall_identifiers.values() if isinstance(values, list) for value in values]
    overlap = sorted(set(visible) & set(candidates))
    return {"inventory_item_id": item.get("id"), "overlap": overlap, "category": "SEMANTIC_OR_VISUAL_REVIEW", "requires_human_review": True}


def propose_incident_actions(matches: list[dict[str, Any]]) -> dict[str, Any]:
    """Propose only reversible holds and human reviews from validated match categories."""
    return {
        "quarantine_holds": [m.get("inventory_item_id") for m in matches if m.get("category") == "EXACT_MATCH"],
        "human_reviews": [m.get("inventory_item_id") for m in matches if m.get("category") in {"IDENTIFIER_REVIEW", "SEMANTIC_OR_VISUAL_REVIEW", "INSUFFICIENT_DATA"}],
        "prohibited_actions": ["dispose", "public_alert", "declare_safe"],
    }


def create_partner_tasks(agency_ids: list[str], exact_item_ids: list[str], review_item_ids: list[str]) -> dict[str, Any]:
    """Return a task proposal only; the application service performs authorized writes."""
    return {
        "proposals": [
            {"agency_id": agency, "required_action": "review_and_acknowledge", "reversible_only": True}
            for agency in sorted(set(agency_ids))
        ],
        "exact_item_ids": exact_item_ids,
        "review_item_ids": review_item_ids,
        "write_performed": False,
    }


def get_incident_status(incident: dict[str, Any]) -> dict[str, Any]:
    """Return sanitized incident status for planning."""
    return _sanitize(incident)


def summarize_open_actions(tasks: list[dict[str, Any]]) -> dict[str, Any]:
    """Summarize open partner acknowledgements from sanitized task records."""
    open_tasks = [_sanitize(task) for task in tasks if task.get("status") not in {"ACKNOWLEDGED", "RESOLVED"}]
    return {"open_action_count": len(open_tasks), "open_actions": open_tasks[:100], "truncated": len(open_tasks) > 100}


ALL_TOOLS = [
    load_recall_source,
    extract_recall_fields,
    query_inventory,
    evaluate_ambiguous_item,
    propose_incident_actions,
    create_partner_tasks,
    get_incident_status,
    summarize_open_actions,
]
