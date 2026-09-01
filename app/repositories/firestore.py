from __future__ import annotations

from typing import Any

from app.domain.enums import ConfidenceCategory, IncidentState, InventoryStatus, MatchCategory, TaskStatus
from app.domain.models import (
    Agency,
    AuditEvent,
    Incident,
    InventoryItem,
    MatchDecision,
    PartnerTask,
    Recall,
    RecallSource,
)

from .base import Repository


class FirestoreRepository(Repository):
    """Firestore adapter with typed domain hydration and transactional idempotency."""

    MODELS = {
        "agencies": Agency,
        "recall_sources": RecallSource,
        "recalls": Recall,
        "inventory": InventoryItem,
        "incidents": Incident,
        "matches": MatchDecision,
        "tasks": PartnerTask,
        "audit_events": AuditEvent,
    }

    def __init__(self, project: str | None = None, database: str = "(default)") -> None:
        try:
            from google.cloud import firestore
        except ImportError as exc:
            raise RuntimeError("Install google-cloud-firestore to use FirestoreRepository") from exc
        self._firestore = firestore
        kwargs: dict[str, Any] = {"database": database}
        if project:
            kwargs["project"] = project
        self.db = firestore.Client(**kwargs)

    @staticmethod
    def _payload(value: Any) -> dict[str, Any]:
        return value.to_dict() if hasattr(value, "to_dict") else dict(value)

    @classmethod
    def _hydrate(cls, collection: str, value: dict[str, Any] | None):
        if value is None or collection not in cls.MODELS:
            return value
        data = dict(value)
        if collection == "inventory":
            data["status"] = InventoryStatus(data.get("status", "AVAILABLE"))
        if collection == "incidents":
            data["state"] = IncidentState(data.get("state", "RECEIVED"))
        if collection == "matches":
            data["category"] = MatchCategory(data["category"])
            data["confidence_category"] = ConfidenceCategory(data["confidence_category"])
        if collection == "tasks":
            data["status"] = TaskStatus(data.get("status", "OPEN"))
        return cls.MODELS[collection](**data)

    def put(self, collection: str, key: str, value: Any) -> None:
        self.db.collection(collection).document(key).set(self._payload(value))

    def get(self, collection: str, key: str):
        snapshot = self.db.collection(collection).document(key).get()
        return self._hydrate(collection, snapshot.to_dict() if snapshot.exists else None)

    def list(self, collection: str) -> list[Any]:
        return [self._hydrate(collection, doc.to_dict()) for doc in self.db.collection(collection).stream()]

    def find_one(self, collection: str, field: str, value: Any):
        docs = self.db.collection(collection).where(filter=self._firestore.FieldFilter(field, "==", value)).limit(1).stream()
        for doc in docs:
            return self._hydrate(collection, doc.to_dict())
        return None

    def create_if_absent(self, collection: str, unique_field: str, unique_value: Any, key: str, value: Any) -> tuple[Any, bool]:
        doc_ref = self.db.collection(collection).document(key)
        transaction = self.db.transaction()

        @self._firestore.transactional
        def txn(txn_obj):
            query = self.db.collection(collection).where(filter=self._firestore.FieldFilter(unique_field, "==", unique_value)).limit(1)
            existing = list(query.stream(transaction=txn_obj))
            if existing:
                return self._hydrate(collection, existing[0].to_dict()), False
            txn_obj.set(doc_ref, self._payload(value))
            return value, True

        return txn(transaction)

    def reset(self) -> None:
        for collection in ["audit_events", "tasks", "matches", "incidents", "inventory", "recalls", "recall_sources", "agencies"]:
            for doc in self.db.collection(collection).stream():
                doc.reference.delete()
