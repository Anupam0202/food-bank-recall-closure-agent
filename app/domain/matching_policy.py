from __future__ import annotations

import re
from dataclasses import dataclass

from .enums import ConfidenceCategory, MatchCategory
from .models import InventoryItem, Recall


def normalize_upc(value: str | None) -> str:
    return re.sub(r"\D", "", value or "")


def normalize_lot(value: str | None) -> str:
    return re.sub(r"[^A-Z0-9]", "", (value or "").upper())


def normalize_text(value: str | None) -> str:
    return " ".join(re.findall(r"[a-z0-9]+", (value or "").lower()))


@dataclass(frozen=True)
class PolicyDecision:
    category: MatchCategory
    confidence: ConfidenceCategory
    matched_fields: list[str]
    evidence: list[str]
    auto_quarantine: bool


def decide_match(recall: Recall, item: InventoryItem) -> PolicyDecision:
    item_upc = normalize_upc(item.upc)
    recall_upcs = {normalize_upc(v) for v in recall.upc_candidates if normalize_upc(v)}
    item_lot = normalize_lot(item.lot_code)
    recall_lots = {normalize_lot(v) for v in recall.lot_codes if normalize_lot(v)}

    upc_exact = bool(item_upc and item_upc in recall_upcs)
    lot_exact = bool(item_lot and item_lot in recall_lots)
    matched: list[str] = []
    if upc_exact:
        matched.append("upc")
    if lot_exact:
        matched.append("lot_code")

    if upc_exact and lot_exact:
        return PolicyDecision(
            MatchCategory.EXACT_MATCH,
            ConfidenceCategory.SOURCE_EXACT,
            matched,
            ["Exact normalized UPC and lot-code match"],
            True,
        )

    if upc_exact or lot_exact:
        missing = "lot code" if upc_exact and not lot_exact else "complete product identifier"
        return PolicyDecision(
            MatchCategory.IDENTIFIER_REVIEW,
            ConfidenceCategory.AMBIGUOUS,
            matched,
            [f"One source identifier matched; {missing} requires human verification"],
            False,
        )

    item_text = normalize_text(f"{item.brand} {item.name}")
    recall_text = normalize_text(f"{' '.join(recall.brands)} {recall.product_description}")
    overlap = set(item_text.split()) & set(recall_text.split())
    meaningful = {w for w in overlap if len(w) > 3}
    if meaningful:
        return PolicyDecision(
            MatchCategory.SEMANTIC_OR_VISUAL_REVIEW,
            ConfidenceCategory.SOURCE_INFERRED,
            [],
            [f"Text overlap requires review: {', '.join(sorted(meaningful)[:4])}"],
            False,
        )

    if not item.upc and not item.lot_code and not item.image_uri:
        return PolicyDecision(
            MatchCategory.INSUFFICIENT_DATA,
            ConfidenceCategory.MISSING,
            [],
            ["No stable identifier or package image is available"],
            False,
        )

    return PolicyDecision(
        MatchCategory.NO_MATCH,
        ConfidenceCategory.SOURCE_EXACT,
        [],
        ["No deterministic identifier or meaningful product-text match"],
        False,
    )
