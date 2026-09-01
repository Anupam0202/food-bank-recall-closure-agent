from __future__ import annotations

import hashlib
import hmac
import json
import secrets
import warnings
from io import BytesIO
from pathlib import Path

from app.domain.exceptions import AuthorizationError, ValidationError

DOCUMENT_EXTENSIONS = {"application/pdf": {".pdf"}, "application/json": {".json"}, "text/plain": {".txt", ".text"}}
IMAGE_EXTENSIONS = {"image/png": {".png"}, "image/jpeg": {".jpg", ".jpeg"}, "image/webp": {".webp"}}
SIGNATURES = {"application/pdf": b"%PDF", "image/png": b"\x89PNG\r\n\x1a\n", "image/jpeg": b"\xff\xd8\xff", "image/webp": b"RIFF"}
IMAGE_FORMATS = {"image/png": "PNG", "image/jpeg": "JPEG", "image/webp": "WEBP"}


def verify_secret(provided: str | None, expected: str) -> bool:
    return bool(provided) and hmac.compare_digest(provided.encode(), expected.encode())


def new_csrf_token() -> str:
    return secrets.token_urlsafe(32)


def require_admin(session: dict) -> None:
    if not session.get("is_admin"):
        raise AuthorizationError("Administrator authentication required")


def require_csrf(session: dict, provided: str | None) -> None:
    expected = session.get("csrf_token")
    if not expected or not provided or not hmac.compare_digest(expected, provided):
        raise AuthorizationError("Invalid CSRF token")


def safe_filename(original: str) -> str:
    suffix = Path(original or "upload").suffix.lower()
    return f"{secrets.token_hex(16)}{suffix}"


def safe_public_error(exc: Exception) -> str:
    if isinstance(exc, ValidationError):
        return str(exc)
    return "The request could not be processed safely; inspect the sanitized audit log."


def validate_upload(data: bytes, content_type: str, kind: str, max_bytes: int, filename: str | None = None) -> None:
    if not data:
        raise ValidationError("The uploaded file is empty")
    if len(data) > max_bytes:
        raise ValidationError("The uploaded file exceeds the configured limit")
    allowed = IMAGE_EXTENSIONS if kind == "image" else DOCUMENT_EXTENSIONS
    if content_type not in allowed:
        raise ValidationError("Unsupported file type")
    suffix = Path(filename or "").suffix.lower()
    if filename and suffix not in allowed[content_type]:
        raise ValidationError("File extension does not match its declared type")
    signature = SIGNATURES.get(content_type)
    if signature and not data.startswith(signature):
        raise ValidationError("File signature does not match its declared type")

    if kind == "image":
        try:
            from PIL import Image
            Image.MAX_IMAGE_PIXELS = 36_000_000
            with warnings.catch_warnings():
                warnings.simplefilter("error", Image.DecompressionBombWarning)
                image = Image.open(BytesIO(data))
                if image.format != IMAGE_FORMATS[content_type]:
                    raise ValidationError("Decoded image format does not match its declared type")
                width, height = image.size
                if width > 6000 or height > 6000:
                    raise ValidationError("Image dimensions exceed 6000 × 6000")
                image.verify()
        except ValidationError:
            raise
        except Exception as exc:
            raise ValidationError("Image cannot be decoded safely") from exc
    elif content_type == "application/json":
        try:
            value = json.loads(data.decode("utf-8"))
            if not isinstance(value, (dict, list)):
                raise ValueError
        except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
            raise ValidationError("JSON upload must contain a UTF-8 object or array") from exc
    elif content_type == "text/plain":
        try:
            text = data.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise ValidationError("Text upload must be valid UTF-8") from exc
        if "\x00" in text:
            raise ValidationError("Text upload contains unsupported null bytes")
    elif content_type == "application/pdf":
        try:
            from pypdf import PdfReader
            reader = PdfReader(BytesIO(data), strict=True)
            if reader.is_encrypted or len(reader.pages) == 0 or len(reader.pages) > 100:
                raise ValidationError("PDF must be unencrypted and contain 1–100 readable pages")
        except ValidationError:
            raise
        except Exception as exc:
            raise ValidationError("PDF cannot be parsed safely") from exc


def payload_hash(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()
