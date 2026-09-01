from __future__ import annotations

from typing import Any


def status_payload(settings: Any) -> dict[str, Any]:
    return {
        "status": "ok",
        "ai_mode": settings.ai_label,
        "model": settings.model_name,
        "repository": settings.repository_label,
        "media": settings.media_label,
        "deployment_target": settings.deployment_target,
        "serverless": settings.serverless,
        "durable_state": settings.durable_state,
        "pubsub": bool(settings.pubsub_verification_audience),
        "revision": settings.deployed_revision or "local",
    }
