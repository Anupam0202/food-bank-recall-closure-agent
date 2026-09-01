from __future__ import annotations

from typing import Any

FREE_STORAGE_REGIONS = {"us-central1", "us-east1", "us-west1"}
FREE_TIER_LIMITS = [
    {"service": "Cloud Run", "limit": "2M requests/month + request-based compute allowance"},
    {"service": "Firestore", "limit": "1 GiB; 50K reads, 20K writes, 20K deletes/day"},
    {"service": "Cloud Storage", "limit": "5 GB-month in us-central1/us-east1/us-west1"},
    {"service": "Pub/Sub", "limit": "10 GiB messages/month"},
    {"service": "Secret Manager", "limit": "6 active versions + 10K accesses/month"},
]


def _check(key: str, label: str, passed: bool, detail: str, action: str) -> dict[str, Any]:
    return {"key": key, "label": label, "passed": passed, "detail": detail, "action": action}


def readiness_payload(settings: Any) -> dict[str, Any]:
    """Return redacted local, hosted-preview, and Google Cloud readiness."""

    local_checks = [
        _check("mode", "Deterministic demo mode", settings.ai_mode in {"mock", "replay", "live"}, settings.ai_label, "Set AI_MODE=mock for a zero-network demo."),
        _check("repository", "Local-safe repository", not settings.use_firestore or bool(settings.google_cloud_project), settings.repository_label, "Use in-memory locally or configure a project for Firestore."),
        _check("media", "Local-safe evidence store", not settings.use_cloud_storage or bool(settings.gcs_bucket), settings.media_label, "Use local media locally or configure a private bucket."),
    ]
    hosted_checks = [
        _check("target", "Vercel deployment target", settings.deployment_target == "vercel", settings.deployment_target, "Set DEPLOYMENT_TARGET=vercel."),
        _check("https", "HTTPS public URL", settings.app_base_url.startswith("https://"), "HTTPS" if settings.app_base_url.startswith("https://") else "Not HTTPS", "Set APP_BASE_URL to the production .vercel.app URL."),
        _check("session", "Strong session secret", len(settings.session_secret) >= 32 and settings.session_secret != "development-only-change-me", "Configured" if len(settings.session_secret) >= 32 and settings.session_secret != "development-only-change-me" else "Development value", "Generate a random 32+ character value."),
        _check("admin", "Private administrator token", len(settings.demo_admin_token) >= 12 and settings.demo_admin_token != "demo-admin", "Configured" if len(settings.demo_admin_token) >= 12 and settings.demo_admin_token != "demo-admin" else "Development value", "Generate a random private token."),
        _check("payload", "Vercel-compatible upload limits", max(settings.max_document_bytes, settings.max_image_bytes) <= 4_000_000, f"{max(settings.max_document_bytes, settings.max_image_bytes)} bytes", "Set both upload limits to 4000000 or less."),
    ]
    cloud_checks = [
        _check("project", "Google Cloud project", bool(settings.google_cloud_project), "Configured" if settings.google_cloud_project else "Not configured", "Set GOOGLE_CLOUD_PROJECT."),
        _check("gemini", "Live Gemini credentials", settings.ai_mode == "live" and bool(settings.gemini_api_key), "Configured" if settings.ai_mode == "live" and settings.gemini_api_key else "Mock/replay or key missing", "Set AI_MODE=live and provide GEMINI_API_KEY through Secret Manager."),
        _check("firestore", "Durable Firestore", settings.use_firestore and bool(settings.google_cloud_project), "Enabled" if settings.use_firestore else "Disabled", "Set USE_FIRESTORE=true."),
        _check("storage", "Private Cloud Storage", settings.use_cloud_storage and bool(settings.gcs_bucket), "Enabled" if settings.use_cloud_storage else "Disabled", "Set USE_CLOUD_STORAGE=true and GCS_BUCKET."),
        _check("pubsub", "Authenticated Pub/Sub push", bool(settings.pubsub_verification_audience) and str(settings.pubsub_verification_audience).startswith("https://"), "Configured" if settings.pubsub_verification_audience else "Not configured", "Set the Cloud Run URL as PUBSUB_VERIFICATION_AUDIENCE."),
        _check("session", "Strong session secret", len(settings.session_secret) >= 32 and settings.session_secret != "development-only-change-me", "Configured" if len(settings.session_secret) >= 32 and settings.session_secret != "development-only-change-me" else "Development value", "Store a random 32+ character value in Secret Manager."),
        _check("admin", "Private administrator token", len(settings.demo_admin_token) >= 12 and settings.demo_admin_token != "demo-admin", "Configured" if len(settings.demo_admin_token) >= 12 and settings.demo_admin_token != "demo-admin" else "Development value", "Store a random private token in Secret Manager."),
        _check("url", "HTTPS service URL", settings.app_base_url.startswith("https://"), "HTTPS" if settings.app_base_url.startswith("https://") else "Local HTTP", "Deploy to Cloud Run and set APP_BASE_URL."),
    ]
    cloud_passed = sum(1 for item in cloud_checks if item["passed"])
    hosted_passed = sum(1 for item in hosted_checks if item["passed"])
    local_ready = all(item["passed"] for item in local_checks)
    cloud_ready = cloud_passed == len(cloud_checks)
    hosted_ready = hosted_passed == len(hosted_checks)
    status = "CLOUD_READY" if cloud_ready else "HOSTED_PREVIEW_READY" if hosted_ready else "LOCAL_READY" if local_ready else "CONFIGURATION_NEEDED"
    return {
        "status": status,
        "local_demo": {"ready": local_ready, "checks": local_checks},
        "hosted_preview": {
            "ready": hosted_ready,
            "score": round(100 * hosted_passed / len(hosted_checks)),
            "passed": hosted_passed,
            "total": len(hosted_checks),
            "checks": hosted_checks,
            "durability_warning": "Vercel with in-memory state and /tmp media is an ephemeral judge preview. Use the Google Cloud deployment for durable workflow proof.",
        },
        "cloud_deployment": {"ready": cloud_ready, "score": round(100 * cloud_passed / len(cloud_checks)), "passed": cloud_passed, "total": len(cloud_checks), "checks": cloud_checks},
        "cost_guardrails": {
            "profile": settings.cloud_cost_profile,
            "region": settings.google_cloud_region,
            "region_optimized_for_storage_free_tier": settings.google_cloud_region in FREE_STORAGE_REGIONS,
            "max_instances": settings.cloud_run_max_instances,
            "min_instances": 0,
            "request_based_billing": True,
            "limits": FREE_TIER_LIMITS,
            "warning": "A billing account is required for Google Cloud Free Tier. Budgets alert; they do not automatically cap charges.",
        },
        "safe_configuration": {
            "model": settings.model_name,
            "deployment_target": settings.deployment_target,
            "serverless": settings.serverless,
            "durable_state": settings.durable_state,
            "firestore_database": settings.firestore_database,
            "project_configured": bool(settings.google_cloud_project),
            "bucket_configured": bool(settings.gcs_bucket),
            "gemini_key_configured": bool(settings.gemini_api_key),
            "pubsub_audience_configured": bool(settings.pubsub_verification_audience),
        },
    }
