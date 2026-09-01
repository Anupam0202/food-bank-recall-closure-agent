from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class Repository(ABC):
    @abstractmethod
    def put(self, collection: str, key: str, value: Any) -> None: ...

    @abstractmethod
    def get(self, collection: str, key: str) -> Any | None: ...

    @abstractmethod
    def list(self, collection: str) -> list[Any]: ...

    @abstractmethod
    def find_one(self, collection: str, field: str, value: Any) -> Any | None: ...

    @abstractmethod
    def reset(self) -> None: ...
