from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:  # The offline core intentionally works without optional packages.
    load_dotenv = None

if load_dotenv is not None:
    load_dotenv(dotenv_path=Path.cwd() / ".env", override=False)


def _text(name: str, default: str = "") -> str:
    return os.getenv(name, default)


def _optional(name: str) -> str | None:
    value = os.getenv(name, "").strip()
    return value or None


def _bool(name: str, default: bool = False) -> bool:
    return os.getenv(name, str(default)).strip().lower() in {"1", "true", "yes", "on"}


def _int(name: str, default: int) -> int:
    return int(os.getenv(name, str(default)))


def _default_app_env() -> str:
    return _text("APP_ENV", "demo" if _bool("VERCEL") else "development").lower()


def _default_deployment_target() -> str:
    explicit = _text("DEPLOYMENT_TARGET", "").strip().lower()
    if explicit:
        return explicit
    if _bool("VERCEL"):
        return "vercel"
    if _optional("K_SERVICE"):
        return "cloud-run"
    return "local"


def _default_base_url() -> str:
    explicit = _text("APP_BASE_URL", "").strip()
    if explicit:
        return explicit
    vercel_url = _text("VERCEL_URL", "").strip()
    return "https://" + vercel_url if vercel_url else "http://localhost:8080"


def _default_upload_dir() -> str:
    explicit = _text("RUNTIME_UPLOAD_DIR", "").strip()
    if explicit:
        return explicit
    return "/tmp/recall-closure/uploads" if _bool("VERCEL") else "runtime/uploads"


def _default_revision() -> str | None:
    value = _optional("K_REVISION") or _optional("VERCEL_GIT_COMMIT_SHA")
    return value[:16] if value else None


@dataclass(frozen=True)
class Settings:
    """Environment-backed settings evaluated when each instance is created."""

    app_env: str = field(default_factory=_default_app_env)
    deployment_target: str = field(default_factory=_default_deployment_target)
    port: int = field(default_factory=lambda: _int("PORT", 8080))
    app_base_url: str = field(default_factory=_default_base_url)
    session_secret: str = field(default_factory=lambda: _text("SESSION_SECRET", "development-only-change-me"))
    demo_admin_token: str = field(default_factory=lambda: _text("DEMO_ADMIN_TOKEN", "demo-admin"))
    ai_mode: str = field(default_factory=lambda: _text("AI_MODE", "mock").lower())
    model_name: str = field(default_factory=lambda: _text("MODEL_NAME", "gemini-3.7-flash"))
    gemini_api_key: str | None = field(default_factory=lambda: _optional("GEMINI_API_KEY"))
    google_cloud_project: str | None = field(default_factory=lambda: _optional("GOOGLE_CLOUD_PROJECT"))
    google_cloud_region: str = field(default_factory=lambda: _text("GOOGLE_CLOUD_REGION", "us-central1"))
    firestore_database: str = field(default_factory=lambda: _text("FIRESTORE_DATABASE", "(default)"))
    use_firestore: bool = field(default_factory=lambda: _bool("USE_FIRESTORE"))
    gcs_bucket: str | None = field(default_factory=lambda: _optional("GCS_BUCKET"))
    use_cloud_storage: bool = field(default_factory=lambda: _bool("USE_CLOUD_STORAGE"))
    pubsub_verification_audience: str | None = field(default_factory=lambda: _optional("PUBSUB_VERIFICATION_AUDIENCE"))
    max_document_bytes: int = field(default_factory=lambda: _int("MAX_DOCUMENT_BYTES", 10 * 1024 * 1024))
    max_image_bytes: int = field(default_factory=lambda: _int("MAX_IMAGE_BYTES", 8 * 1024 * 1024))
    runtime_upload_dir: str = field(default_factory=_default_upload_dir)
    model_max_attempts: int = field(default_factory=lambda: _int("MODEL_MAX_ATTEMPTS", 3))
    log_level: str = field(default_factory=lambda: _text("LOG_LEVEL", "INFO"))
    cloud_cost_profile: str = field(default_factory=lambda: _text("CLOUD_COST_PROFILE", "free-tier").lower())
    cloud_run_max_instances: int = field(default_factory=lambda: _int("CLOUD_RUN_MAX_INSTANCES", 1))
    deployed_revision: str | None = field(default_factory=_default_revision)

    @property
    def ai_label(self) -> str:
        return {"live": "LIVE_GEMINI", "mock": "MOCK_GEMINI", "replay": "REPLAY"}.get(self.ai_mode, "INVALID")

    @property
    def repository_label(self) -> str:
        return "FIRESTORE" if self.use_firestore else "IN_MEMORY"

    @property
    def media_label(self) -> str:
        return "CLOUD_STORAGE" if self.use_cloud_storage else "EPHEMERAL_MEDIA" if self.serverless else "LOCAL_MEDIA"

    @property
    def secure_http(self) -> bool:
        return self.app_env in {"demo", "production"}

    @property
    def serverless(self) -> bool:
        return self.deployment_target == "vercel"

    @property
    def durable_state(self) -> bool:
        return self.use_firestore

    def validate(self) -> None:
        if self.app_env not in {"development", "test", "demo", "production"}:
            raise ValueError("APP_ENV must be development, test, demo, or production")
        if self.deployment_target not in {"local", "cloud-run", "vercel"}:
            raise ValueError("DEPLOYMENT_TARGET must be local, cloud-run, or vercel")
        if self.ai_mode not in {"live", "mock", "replay"}:
            raise ValueError("AI_MODE must be live, mock, or replay")
        if not self.model_name.startswith("gemini-"):
            raise ValueError("MODEL_NAME must identify a Gemini model")
        if not 1 <= self.model_max_attempts <= 5:
            raise ValueError("MODEL_MAX_ATTEMPTS must be between 1 and 5")
        if not 1 <= self.cloud_run_max_instances <= 20:
            raise ValueError("CLOUD_RUN_MAX_INSTANCES must be between 1 and 20")
        if self.cloud_cost_profile not in {"free-tier", "standard"}:
            raise ValueError("CLOUD_COST_PROFILE must be free-tier or standard")
        if self.max_document_bytes <= 0 or self.max_image_bytes <= 0:
            raise ValueError("Upload byte limits must be positive")
        if self.ai_mode == "live" and not self.gemini_api_key:
            raise ValueError("GEMINI_API_KEY is required in live mode")
        if self.use_firestore and not self.google_cloud_project:
            raise ValueError("GOOGLE_CLOUD_PROJECT is required with Firestore")
        if self.use_cloud_storage and not self.gcs_bucket:
            raise ValueError("GCS_BUCKET is required with Cloud Storage")
        if self.secure_http:
            if len(self.session_secret) < 32 or self.session_secret == "development-only-change-me":
                raise ValueError("Hosted SESSION_SECRET must be at least 32 random characters")
            if len(self.demo_admin_token) < 12 or self.demo_admin_token == "demo-admin":
                raise ValueError("Hosted DEMO_ADMIN_TOKEN must be replaced")
            if not self.app_base_url.startswith("https://"):
                raise ValueError("Hosted APP_BASE_URL must use HTTPS")
        if self.serverless and max(self.max_document_bytes, self.max_image_bytes) > 4_000_000:
            raise ValueError("Vercel uploads must stay at or below 4,000,000 bytes because function payloads are limited to 4.5 MB")
        if self.app_env == "production":
            if self.ai_mode != "live":
                raise ValueError("Production requires AI_MODE=live")
            if not self.use_firestore or not self.google_cloud_project:
                raise ValueError("Production requires Firestore and GOOGLE_CLOUD_PROJECT")
            if not self.use_cloud_storage or not self.gcs_bucket:
                raise ValueError("Production requires Cloud Storage and GCS_BUCKET")
            if not self.pubsub_verification_audience:
                raise ValueError("Production requires PUBSUB_VERIFICATION_AUDIENCE")
            if not self.pubsub_verification_audience.startswith("https://"):
                raise ValueError("Production PUBSUB_VERIFICATION_AUDIENCE must use HTTPS")


settings = Settings()
