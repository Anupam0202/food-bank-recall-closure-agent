from __future__ import annotations

from copy import deepcopy
from threading import RLock
from typing import Any

from .base import Repository


class InMemoryRepository(Repository):
    def __init__(self) -> None:
        self._data: dict[str, dict[str, Any]] = {}
        self._lock = RLock()

    def put(self, collection: str, key: str, value: Any) -> None:
        with self._lock:
            self._data.setdefault(collection, {})[key] = deepcopy(value)

    def get(self, collection: str, key: str) -> Any | None:
        with self._lock:
            value = self._data.get(collection, {}).get(key)
            return deepcopy(value)

    def list(self, collection: str) -> list[Any]:
        with self._lock:
            return [deepcopy(v) for v in self._data.get(collection, {}).values()]

    def find_one(self, collection: str, field: str, value: Any) -> Any | None:
        with self._lock:
            for item in self._data.get(collection, {}).values():
                candidate = getattr(item, field, None) if not isinstance(item, dict) else item.get(field)
                if candidate == value:
                    return deepcopy(item)
        return None

    def create_if_absent(self, collection: str, unique_field: str, unique_value: Any, key: str, value: Any) -> tuple[Any, bool]:
        with self._lock:
            existing = self.find_one(collection, unique_field, unique_value)
            if existing is not None:
                return existing, False
            self._data.setdefault(collection, {})[key] = deepcopy(value)
            return deepcopy(value), True

    def reset(self) -> None:
        with self._lock:
            self._data.clear()
