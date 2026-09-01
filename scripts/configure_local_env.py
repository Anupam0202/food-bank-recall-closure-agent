#!/usr/bin/env python3
"""Create a safe local .env without printing generated secrets."""
from __future__ import annotations

import argparse
import getpass
import os
import secrets
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def values(live: bool, api_key: str = "") -> dict[str, str]:
    return {
        "APP_ENV": "development",
        "DEPLOYMENT_TARGET": "local",
        "PORT": "8080",
        "APP_BASE_URL": "http://localhost:8080",
        "SESSION_SECRET": secrets.token_urlsafe(48),
        "DEMO_ADMIN_TOKEN": secrets.token_urlsafe(24),
        "AI_MODE": "live" if live else "mock",
        "MODEL_NAME": "gemini-3.7-flash",
        "MODEL_MAX_ATTEMPTS": "3",
        "GEMINI_API_KEY": api_key if live else "",
        "GOOGLE_CLOUD_PROJECT": "",
        "GOOGLE_CLOUD_REGION": "us-central1",
        "FIRESTORE_DATABASE": "(default)",
        "USE_FIRESTORE": "false",
        "GCS_BUCKET": "",
        "USE_CLOUD_STORAGE": "false",
        "PUBSUB_VERIFICATION_AUDIENCE": "",
        "CLOUD_COST_PROFILE": "free-tier",
        "CLOUD_RUN_MAX_INSTANCES": "1",
        "MAX_DOCUMENT_BYTES": "10485760",
        "MAX_IMAGE_BYTES": "8388608",
        "RUNTIME_UPLOAD_DIR": "runtime/uploads",
        "LOG_LEVEL": "INFO",
    }


def serialize(items: dict[str, str]) -> str:
    return "\n".join(f"{key}={value}" for key, value in items.items()) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true", help="Use a Gemini Developer API key while keeping data and media local")
    parser.add_argument("--force", action="store_true", help="Replace an existing .env")
    args = parser.parse_args()
    target = ROOT / ".env"
    if target.exists() and not args.force:
        raise SystemExit(".env already exists; use --force only after backing it up")
    api_key = ""
    if args.live:
        api_key = os.getenv("GEMINI_API_KEY", "") or getpass.getpass("Gemini API key (input hidden): ").strip()
        if not api_key:
            raise SystemExit("A Gemini API key is required with --live")
    target.write_text(serialize(values(args.live, api_key)), encoding="utf-8")
    try:
        target.chmod(0o600)
    except OSError:
        pass
    print(f"Created {target.name} for {'local live Gemini' if args.live else 'zero-network mock'} mode.")
    print("Generated SESSION_SECRET and DEMO_ADMIN_TOKEN were written but not displayed.")


if __name__ == "__main__":
    main()
