#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
REQUIRED_ENV = [
    "APP_ENV", "DEPLOYMENT_TARGET", "APP_BASE_URL", "SESSION_SECRET",
    "DEMO_ADMIN_TOKEN", "AI_MODE", "MODEL_NAME", "MAX_DOCUMENT_BYTES",
    "MAX_IMAGE_BYTES", "RUNTIME_UPLOAD_DIR",
]


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate Vercel source configuration without exposing secrets")
    parser.add_argument("--check-env", action="store_true", help="also validate the current environment")
    args = parser.parse_args()
    vercel = json.loads((ROOT / "vercel.json").read_text(encoding="utf-8"))
    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    function = vercel.get("functions", {}).get("app/main.py", {})
    errors: list[str] = []
    if project.get("tool", {}).get("vercel", {}).get("entrypoint") != "app.main:app":
        errors.append("tool.vercel.entrypoint must be app.main:app")
    if not 1 <= int(function.get("maxDuration", 0)) <= 300:
        errors.append("app/main.py maxDuration must be within the Vercel Hobby limit")
    if not (ROOT / ".python-version").read_text().strip() == "3.12":
        errors.append(".python-version must be 3.12")
    environment = "not_checked"
    if args.check_env:
        from app.config import Settings
        try:
            settings = Settings()
            settings.validate()
            if settings.deployment_target != "vercel" or settings.app_env != "demo":
                raise ValueError("Use APP_ENV=demo and DEPLOYMENT_TARGET=vercel for the public preview")
            environment = "passed"
        except Exception as exc:
            errors.append(str(exc))
            environment = "failed"
    result = {
        "status": "PASS" if not errors else "FAIL",
        "entrypoint": project.get("tool", {}).get("vercel", {}).get("entrypoint"),
        "max_duration_seconds": function.get("maxDuration"),
        "python": "3.12",
        "environment": environment,
        "required_environment_names": REQUIRED_ENV,
        "secrets_printed": False,
        "errors": errors,
    }
    print(json.dumps(result, indent=2))
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
