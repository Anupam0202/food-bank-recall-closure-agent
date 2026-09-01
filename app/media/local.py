from pathlib import Path

from .base import MediaStore


class LocalMediaStore(MediaStore):
    def __init__(self, root: str = "runtime/uploads") -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def save(self, name: str, data: bytes, content_type: str) -> str:
        target = self.root / name
        target.write_bytes(data)
        return f"/media/{name}"
