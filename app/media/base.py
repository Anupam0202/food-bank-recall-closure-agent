from abc import ABC, abstractmethod


class MediaStore(ABC):
    @abstractmethod
    def save(self, name: str, data: bytes, content_type: str) -> str: ...
