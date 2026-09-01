#!/usr/bin/env python3
"""Collect and validate non-secret Google Cloud deployment identifiers."""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]


def run(*args: str) -> tuple[bool, str]:
    result = subprocess.run(["gcloud", *args], capture_output=True, text=True)
    return result.returncode == 0, (result.stdout or result.stderr).strip()


def value(*args: str) -> str | None:
    ok, output = run(*args)
    return output if ok and output and output != "(unset)" else None


def exists(*args: str) -> bool:
    ok, _ = run(*args)
    return ok


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", help="Project ID; defaults to active gcloud project")
    parser.add_argument("--region", default="us-central1")
    parser.add_argument("--service", default="recall-closure-agent")
    parser.add_argument("--output", default=str(ROOT / "gcp-readiness.json"))
    parser.add_argument("--write-env-template", action="store_true")
    args = parser.parse_args()
    if not shutil.which("gcloud"):
        raise SystemExit("gcloud is not installed. Use Google Cloud Shell or install the Google Cloud CLI.")

    active_account = value("auth", "list", "--filter=status:ACTIVE", "--format=value(account)")
    project = args.project or value("config", "get-value", "project")
    if not project:
        raise SystemExit("No project selected. Run: gcloud config set project YOUR_PROJECT_ID")
    run("config", "set", "project", project)
    project_number = value("projects", "describe", project, "--format=value(projectNumber)")
    billing_ok = exists("billing", "projects", "describe", project)
    service_url = value("run", "services", "describe", args.service, "--region", args.region, "--format=value(status.url)")
    bucket = f"recall-closure-evidence-{project}"
    resources: dict[str, bool] = {
        "firestore_default": exists("firestore", "databases", "describe", "--database=(default)"),
        "storage_bucket": exists("storage", "buckets", "describe", f"gs://{bucket}"),
        "pubsub_topic": exists("pubsub", "topics", "describe", "recall-notices"),
        "pubsub_subscription": exists("pubsub", "subscriptions", "describe", "recall-closure-push"),
        "secret_gemini_api_key": exists("secrets", "describe", "gemini-api-key"),
        "secret_session": exists("secrets", "describe", "session-secret"),
        "secret_admin": exists("secrets", "describe", "demo-admin-token"),
        "cloud_run_service": bool(service_url),
    }
    report: dict[str, Any] = {
        "status": "READY" if active_account and project_number and billing_ok and all(resources.values()) else "INCOMPLETE",
        "active_account_configured": bool(active_account),
        "project_id": project,
        "project_number": project_number,
        "billing_account_linked": billing_ok,
        "region": args.region,
        "service_name": args.service,
        "service_url": service_url,
        "pubsub_verification_audience": service_url,
        "gcs_bucket": bucket,
        "runtime_service_account": f"recall-closure-runtime@{project}.iam.gserviceaccount.com",
        "push_service_account": f"recall-closure-push@{project}.iam.gserviceaccount.com",
        "resources": resources,
        "secret_values_exposed": False,
    }
    output = Path(args.output)
    output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    print(f"Wrote redacted report: {output}")

    if args.write_env_template:
        env = ROOT / ".env.cloud.generated"
        env.write_text(
            "\n".join(
                [
                    "APP_ENV=production",
                    "PORT=8080",
                    f"APP_BASE_URL={service_url or '<set-after-deploy>'}",
                    "SESSION_SECRET=<secret-manager:session-secret>",
                    "DEMO_ADMIN_TOKEN=<secret-manager:demo-admin-token>",
                    "AI_MODE=live",
                    "MODEL_NAME=gemini-3.7-flash",
                    "MODEL_MAX_ATTEMPTS=3",
                    "GEMINI_API_KEY=<secret-manager:gemini-api-key>",
                    f"GOOGLE_CLOUD_PROJECT={project}",
                    f"GOOGLE_CLOUD_REGION={args.region}",
                    "FIRESTORE_DATABASE=(default)",
                    "USE_FIRESTORE=true",
                    f"GCS_BUCKET={bucket}",
                    "USE_CLOUD_STORAGE=true",
                    f"PUBSUB_VERIFICATION_AUDIENCE={service_url or '<set-after-deploy>'}",
                    "CLOUD_COST_PROFILE=free-tier",
                    "CLOUD_RUN_MAX_INSTANCES=1",
                ]
            ) + "\n",
            encoding="utf-8",
        )
        print(f"Wrote non-secret template: {env}")


if __name__ == "__main__":
    main()
