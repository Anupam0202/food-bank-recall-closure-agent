#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import re
import sys
import zipfile
from pathlib import Path, PurePosixPath

ZIP_PATH = Path(sys.argv[1] if len(sys.argv) > 1 else "/data/food-bank-recall-closure-agent.zip")
ROOT = "food-bank-recall-closure-agent/"
REQUIRED = {
    "README.md",
    "LICENSE",
    "Dockerfile",
    "agent.py",
    "app/main.py",
    "app/agents/coordinator.py",
    "app/agents/prompts.py",
    "app/agents/output_schemas.py",
    "app/agents/tools.py",
    "app/workflows/recall_workflow.py",
    "app/workflows/idempotency.py",
    "app/services/gemini_service.py",
    "app/services/pubsub_service.py",
    "app/services/task_service.py",
    "app/services/verification_service.py",
    "app/services/audit_service.py",
    "app/services/evidence_pack_service.py",
    "app/services/readiness_service.py",
    "app/api/ingestion.py",
    "app/api/incidents.py",
    "app/api/tasks.py",
    "app/api/pubsub.py",
    "app/api/media.py",
    "docs/ARCHITECTURE.md",
    "docs/ARCHITECTURE_DECISIONS.md",
    "docs/SECURITY.md",
    "docs/SOURCES.md",
    "docs/DEVPOST_SUBMISSION.md",
    "docs/GOOGLE_CLOUD_FREE_SETUP.md",
    "docs/UPGRADE_SCORECARD.md",
    "docs/RELEASE_NOTES_1.2.0.md",
    "docs/RELEASE_NOTES_1.3.0.md",
    "docs/GITHUB_VERCEL_DEPLOYMENT.md",
    "docs/DEVPOST_FORM_ANSWERS.md",
    "docs/VIDEO_PITCH_4_MIN.md",
    "docs/SUBMISSION_CHECKLIST.md",
    "docs/architecture-diagram.png",
    "vercel.json",
    ".python-version",
    ".vercelignore",
    "docs/screenshots/dashboard-desktop.png",
    "docs/screenshots/dashboard-mobile.png",
    "docs/screenshots/incident-desktop.png",
    "docs/screenshots/partner-tasks-desktop.png",
    "docs/screenshots/readiness-desktop.png",
    "docs/screenshots/readiness-mobile.png",
    "infra/deploy_cloud_run.sh",
    "infra/create_pubsub.sh",
    "scripts/run_golden_path.py",
    "scripts/adk_import_smoke.py",
    "scripts/http_smoke.py",
    "scripts/configure_local_env.py",
    "scripts/gcp_collect_config.py",
    "scripts/verify_evidence_pack.py",
    "scripts/vercel_preflight.py",
    "tests/test_vercel_deployment.py",
    "tests/test_workflow.py",
    "tests/test_evidence_pack.py",
    "tests/test_readiness.py",
    "requirements.txt",
    "requirements-dev.txt",
    "constraints-python312.txt",
    "scripts/setup_windows.cmd",
    "scripts/run_windows.cmd",
    "scripts/check_dependency_compatibility.py",
    "BUILD_STATE.json",
    "BUILD_REPORT.md",
    "release_manifest.json",
}
PROHIBITED_SEGMENTS = {".git", ".venv", "__pycache__", ".pytest_cache", ".ruff_cache", "runtime", "htmlcov"}
PROHIBITED_BASENAMES = {".env", ".coverage", "credentials.json", "service-account.json"}
TEXT_SUFFIXES = {".py", ".md", ".txt", ".json", ".yaml", ".yml", ".toml", ".sh", ".cmd", ".html", ".css", ".js", ".example"}
SECRET_PATTERNS = [
    re.compile(rb"AIza[0-9A-Za-z_-]{30,}"),
    re.compile(rb"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    re.compile(rb'"private_key"\s*:\s*"-----BEGIN'),
    re.compile(rb"(?:GEMINI_API_KEY|SESSION_SECRET|DEMO_ADMIN_TOKEN)=(?![a-z0-9-]+:(?:latest|[0-9]+)\\b)[^\\s#'\"]{12,}"),
]


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> None:
    if not ZIP_PATH.is_file():
        raise SystemExit(f"ZIP not found: {ZIP_PATH}")
    with zipfile.ZipFile(ZIP_PATH) as archive:
        corrupt = archive.testzip()
        if corrupt:
            raise SystemExit(f"Corrupt member: {corrupt}")
        file_infos = [info for info in archive.infolist() if not info.is_dir()]
        if len(file_infos) < 100:
            raise SystemExit(f"Archive unexpectedly small: {len(file_infos)} files")
        total_uncompressed = sum(info.file_size for info in file_infos)
        if total_uncompressed > 100 * 1024 * 1024:
            raise SystemExit("Archive exceeds 100 MiB uncompressed safety limit")

        relative_files: set[str] = set()
        for info in file_infos:
            name = info.filename
            path = PurePosixPath(name)
            if not name.startswith(ROOT) or path.is_absolute() or ".." in path.parts:
                raise SystemExit(f"Unsafe archive path: {name}")
            rel = str(PurePosixPath(name).relative_to(ROOT.rstrip("/")))
            relative_files.add(rel)
            if any(part in PROHIBITED_SEGMENTS for part in path.parts) or path.name in PROHIBITED_BASENAMES:
                raise SystemExit(f"Prohibited archive member: {name}")
            lower = name.lower()
            if lower.endswith((".pem", ".key", ".p12", ".pfx")) or "service-account" in lower:
                raise SystemExit(f"Credential-like archive member: {name}")
            if PurePosixPath(rel).suffix.lower() in TEXT_SUFFIXES and info.file_size <= 2 * 1024 * 1024:
                content = archive.read(info)
                environment_templates = {".env.example", "infra/deploy_cloud_run.sh", "docs/GITHUB_VERCEL_DEPLOYMENT.md"}
                patterns = SECRET_PATTERNS[:3] if rel in environment_templates else SECRET_PATTERNS
                for pattern in patterns:
                    if pattern.search(content):
                        raise SystemExit(f"Possible embedded secret in {name}")

        missing = sorted(REQUIRED - relative_files)
        if missing:
            raise SystemExit(f"Missing archive members: {missing}")

        manifest = json.loads(archive.read(ROOT + "release_manifest.json"))
        if manifest.get("version") != "1.3.0":
            raise SystemExit(f"Unexpected release version: {manifest.get('version')}")
        base_html = archive.read(ROOT + "app/templates/base.html")
        smoke_source = archive.read(ROOT + "scripts/http_smoke.py")
        marker = b'data-app-id="food-bank-recall-closure-agent"'
        if marker not in base_html or marker not in smoke_source:
            raise SystemExit("Semantic HTTP smoke marker contract is missing")
        records = manifest.get("files")
        if not isinstance(records, list) or not records:
            raise SystemExit("Manifest file list is missing")
        manifest_paths = set()
        for record in records:
            rel = record.get("path")
            if not isinstance(rel, str) or rel in manifest_paths:
                raise SystemExit(f"Invalid/duplicate manifest path: {rel!r}")
            manifest_paths.add(rel)
            member = ROOT + rel
            if member not in archive.namelist():
                raise SystemExit(f"Manifest member missing from ZIP: {rel}")
            data = archive.read(member)
            if len(data) != record.get("bytes") or digest(data) != record.get("sha256"):
                raise SystemExit(f"Manifest hash/size mismatch: {rel}")

        expected = relative_files - {"release_manifest.json"}
        if expected != manifest_paths:
            missing_manifest = sorted(expected - manifest_paths)[:10]
            extra_manifest = sorted(manifest_paths - expected)[:10]
            raise SystemExit(f"Manifest scope mismatch; missing={missing_manifest}, extra={extra_manifest}")

    print(
        json.dumps(
            {
                "status": "PASS",
                "zip": str(ZIP_PATH),
                "members": len(file_infos),
                "uncompressed_bytes": total_uncompressed,
                "bytes": ZIP_PATH.stat().st_size,
                "sha256": digest(ZIP_PATH.read_bytes()),
                "required_files": len(REQUIRED),
                "manifest_hashes_verified": len(manifest_paths),
                "secrets_and_exclusions": "PASS",
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
