from __future__ import annotations

from app.domain.matching_policy import PolicyDecision, decide_match
from app.domain.models import InventoryItem, Recall


class InventoryMatcher:
    def evaluate(self, recall: Recall, item: InventoryItem) -> PolicyDecision:
        return decide_match(recall, item)
