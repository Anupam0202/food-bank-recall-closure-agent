from __future__ import annotations

from app.domain.enums import InventoryStatus, MatchCategory, TaskStatus
from app.domain.models import InventoryItem, MatchDecision, PartnerTask


class VerificationService:
    @staticmethod
    def closure_blockers(matches: list[MatchDecision], tasks: list[PartnerTask], inventory: list[InventoryItem]) -> list[str]:
        blockers: list[str] = []
        by_id = {item.id: item for item in inventory}
        unresolved = [match for match in matches if match.category in {
            MatchCategory.IDENTIFIER_REVIEW,
            MatchCategory.SEMANTIC_OR_VISUAL_REVIEW,
            MatchCategory.INSUFFICIENT_DATA,
        } and not match.human_resolution]
        if unresolved:
            blockers.append(f"{len(unresolved)} potential match(es) still require human review")
        exact_not_held = [match for match in matches if match.category == MatchCategory.EXACT_MATCH and (not by_id.get(match.inventory_item_id) or by_id[match.inventory_item_id].status != InventoryStatus.QUARANTINED)]
        if exact_not_held:
            blockers.append(f"{len(exact_not_held)} exact affected item(s) are not on quarantine hold")
        unacknowledged = [task for task in tasks if task.status not in {TaskStatus.ACKNOWLEDGED, TaskStatus.RESOLVED}]
        if unacknowledged:
            blockers.append(f"{len(unacknowledged)} partner acknowledgement(s) missing")
        failed = [task for task in tasks if task.status == TaskStatus.FAILED]
        if failed:
            blockers.append(f"{len(failed)} mandatory partner action(s) failed")
        return blockers
