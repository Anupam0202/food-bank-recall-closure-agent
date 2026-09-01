#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import platform
import subprocess
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
VERSION = "1.3.0"
DEADLINE = datetime(2026, 9, 1, 5, 30, tzinfo=ZoneInfo("Asia/Kolkata"))
EXCLUDED_PARTS = {
    ".git",
    ".venv",
    "__pycache__",
    ".pytest_cache",
    ".ruff_cache",
    "htmlcov",
    "runtime",
    "release-validation",
    "preview",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git_commit() -> str | None:
    result = subprocess.run(["git", "-C", str(ROOT), "rev-parse", "HEAD"], capture_output=True, text=True)
    return result.stdout.strip() if result.returncode == 0 else None


def release_files() -> list[dict[str, object]]:
    records: list[dict[str, object]] = []
    for path in sorted(ROOT.rglob("*")):
        if not path.is_file() or any(part in EXCLUDED_PARTS for part in path.parts):
            continue
        if path.name in {"release_manifest.json", ".coverage", ".env", ".env.cloud.generated", "gcp-readiness.json"}:
            continue
        records.append({"path": str(path.relative_to(ROOT)), "bytes": path.stat().st_size, "sha256": sha256(path)})
    return records


def main() -> None:
    parser = argparse.ArgumentParser(description="Finalize truthful build evidence and release manifest")
    parser.add_argument("--release-validated", action="store_true")
    args = parser.parse_args()
    now = datetime.now(ZoneInfo("Asia/Kolkata"))
    seconds_remaining = int((DEADLINE - now).total_seconds())
    zip_result = "PASS" if args.release_validated else "PENDING"

    phases = {
        "exact_user_tested_baseline_ingested": "passed",
        "starlette_request_first_rendering": "user_verified_passed",
        "brittle_http_title_assertion": "corrected_with_semantic_identity_contract",
        "official_free_tier_and_domain_research": "passed",
        "upgrade_comparison": "passed",
        "settings_and_dotenv_repair": "passed",
        "redacted_readiness_control_plane": "passed",
        "tamper_evident_evidence_pack": "passed_unsigned_integrity",
        "free_tier_deployment_guardrails": "source_validated_not_deployed",
        "unit_tests": "passed_92_discovered_89_passed_3_skipped",
        "golden_path": "passed",
        "dependency_contract": "passed",
        "security_and_repository_scan": "passed",
        "browser_visual_qa": "passed_six_final_captures",
        "vercel_source_preflight": "passed_not_deployed",
        "submission_architecture_diagram": "passed_visual_inspection",
        "full_fastapi_http_smoke_for_1_2_0": "blocked_dependencies_unavailable_in_sandbox",
        "live_gemini": "not_run_no_credentials",
        "docker_build": "not_run_docker_unavailable",
        "google_cloud_deployment": "not_run_no_gcloud_or_credentials",
        "release_packaging": "passed" if args.release_validated else "pending",
        "extracted_release_validation": "passed" if args.release_validated else "pending",
    }
    state = {
        "schema_version": 3,
        "project": "food-bank-recall-closure-agent",
        "version": VERSION,
        "title": "Food-Bank Recall Closure Operations",
        "track": "Taskmaster",
        "generated_at": now.isoformat(timespec="seconds"),
        "deadline": DEADLINE.isoformat(timespec="seconds"),
        "seconds_remaining_at_finalization": seconds_remaining,
        "deadline_status": "before_deadline" if seconds_remaining >= 0 else "after_deadline",
        "operating_mode": "PEAK_RELEASE_HARDENING",
        "phases": phases,
        "selected_upgrades": [
            "Authenticated privacy-minimized evidence ZIP with SHA-256 member manifest",
            "Ordered audit-event hash chain with explicit unsigned-authenticity limitation",
            "Redacted local/cloud readiness UI and JSON API",
            "No-billing local setup plus billing-required Google Cloud Free Tier guide",
            "Scale-to-zero request-based Cloud Run posture with one-instance default",
            "Runtime-evaluated environment settings and local dotenv support",
            "Stable data-app-id and semantic real-server smoke contract",
            "Vercel FastAPI preview profile with fail-closed hosted settings",
            "Copy-ready Devpost form, architecture PNG, and timed video pitch",
        ],
        "safety_invariants": [
            "Only exact normalized UPC and lot identifiers create a reversible quarantine hold",
            "Semantic, visual, partial, and missing-data matches require human review",
            "The application cannot authorize disposal or declare a product safe",
            "Every actioned partner task requires acknowledgement before internal operational closure",
            "Duplicate source records do not duplicate incidents, holds, matches, or tasks",
            "Portable evidence excludes raw uploads and credentials",
            "INTERNAL_CLOSED never represents regulator closure",
        ],
    }
    (ROOT / "BUILD_STATE.json").write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")

    shots = [
        ("dashboard-desktop.png", "1440 × 2098"),
        ("dashboard-mobile.png", "390 × 4286"),
        ("incident-desktop.png", "1440 × 3560"),
        ("partner-tasks-desktop.png", "1440 × 1564"),
        ("readiness-desktop.png", "1440 × 2038"),
        ("readiness-mobile.png", "390 × 3809"),
    ]
    shot_rows = "\n".join(
        f"| `docs/screenshots/{name}` | {dimensions} | `{sha256(ROOT / 'docs/screenshots' / name)}` |"
        for name, dimensions in shots
    )
    report = f"""# Build Report

Generated: `{now.isoformat(timespec='seconds')}`  
Version: `{VERSION}`  
Deadline status: `{state['deadline_status']}` ({seconds_remaining} seconds relative to the recorded hackathon deadline)

## Commands and evidence actually used

| Command or evidence | Real result |
|---|---|
| Exact user-attached release `1.1.2` SHA-256/CRC inspection | PASS — matched `0d78cb6c33acdedca3f0791e1bb3cf60acfe1a7e53098796a7ee284bbce84420` |
| User-reported Windows `python -m unittest discover` on `1.1.2` | PASS — 75 tests, 1 environment-specific skip |
| User-reported Windows real-server requests on `1.1.2` | PASS — `/`, `/healthz`, login, about, inventory, partner tasks, demo action, and incident render returned success/200 where expected |
| User-reported `scripts/http_smoke.py` on `1.1.2` | FAILED assertion only — HTTP 200 HTML was correct; test searched for a title never emitted by the UI |
| `python3 /data/upgrade_peak.py` | PASS — upgrade source applied; initial expanded suite passed 85 tests with 3 skips |
| `python3 /data/polish_peak.py` | PASS — privacy, visual, documentation, and verification polish applied |
| `python3 -m compileall -q app tests scripts` | PASS |
| `python3 -m unittest discover -s tests -v` | PASS — 92 discovered, 89 passed, 3 environment-specific skipped, 0 failed |
| `python3 scripts/check_dependency_compatibility.py` | PASS — pins satisfy Google ADK 2.7.1 Python 3.12 bounds |
| `python3 scripts/run_golden_path.py` | PASS — exact hold, ambiguity review, partner tasks, duplicate suppression, human-gated internal closure, and audit evidence |
| Evidence-pack build and `verify_evidence_pack` unit contracts | PASS — member hashes, root, chain linkage, privacy exclusions, and provisional/final labels |
| `python3 scripts/check_repo.py` | PASS — required files, placeholder scan, and obvious secret scan |
| Jinja parse/render via `python3 scripts/render_static_previews.py` | PASS — dashboard, incident, inventory, partner tasks, and readiness rendered |
| `for f in infra/*.sh scripts/*.sh; do bash -n "$f"; done` | PASS |
| `node --check app/static/app.js` | PASS |
| `markdownlint-cli2 '**/*.md'` | PASS — 0 issues |
| Playwright/Chromium visual contract script for six final pages | PASS — no JavaScript console errors or horizontal overflow; stable app identity present |
| Manual inspection of six final PNGs | PASS — no clipping, overlap, unreadable contrast, or broken responsive layout observed |
| `python3 scripts/http_smoke.py` for `1.3.0` in this sandbox | BLOCKED — FastAPI/Uvicorn packages are unavailable here; the repaired script remains enabled in Windows setup and connected CI |
| `python3 scripts/adk_import_smoke.py` for `1.3.0` in this sandbox | BLOCKED — Google ADK package is unavailable here; the inherited `1.1.2` ADK construction was user-verified on Windows |
| Live Gemini request | NOT RUN — no user credential or explicit paid/live execution was used |
| Docker build | NOT RUN — Docker executable unavailable |
| `bash infra/deploy_cloud_run.sh` | NOT RUN — no gcloud CLI, billing project, or credentials were available |
| `python3 scripts/validate_release.py /data/food-bank-recall-closure-agent.zip` | {zip_result} |
| Clean extracted-copy compile, unit, golden-path, repository, and ZIP validation | {zip_result} |

## Final visual evidence

| File | Dimensions | SHA-256 |
|---|---:|---|
{shot_rows}

## Explicit limitations

- Google Cloud Free Tier requires an active billing account and can charge overages; budget alerts do not cap spend.
- The evidence-pack manifest is unsigned. Its hashes prove self-consistency; signer authenticity requires comparing the root with a separately trusted record.
- No `1.3.0` live Gemini request, Docker build, or Google Cloud deployment was claimed.
- Administrator-token authentication must be replaced by organization identity and agency-scoped authorization before real production use.
- Legal, privacy, retention, accessibility, and real historical matching validation remain organization responsibilities.
"""
    (ROOT / "BUILD_REPORT.md").write_text(report, encoding="utf-8")

    commands = [
        {"name": "compile", "command": "python3 -m compileall -q app tests scripts", "outcome": "passed"},
        {"name": "unittest", "command": "python3 -m unittest discover -s tests -v", "outcome": "passed", "discovered": 92, "passed": 89, "skipped": 3, "failed": 0},
        {"name": "dependency_contract", "command": "python3 scripts/check_dependency_compatibility.py", "outcome": "passed"},
        {"name": "golden_path", "command": "python3 scripts/run_golden_path.py", "outcome": "passed"},
        {"name": "repository_scan", "command": "python3 scripts/check_repo.py", "outcome": "passed"},
        {"name": "template_and_preview", "command": "python3 scripts/render_static_previews.py", "outcome": "passed"},
        {"name": "shell_syntax", "command": "bash -n infra/*.sh scripts/*.sh (iterated)", "outcome": "passed"},
        {"name": "javascript_syntax", "command": "node --check app/static/app.js", "outcome": "passed"},
        {"name": "markdown_lint", "command": "markdownlint-cli2 '**/*.md'", "outcome": "passed"},
        {"name": "visual_qa", "command": "node /data/capture_peak.js", "outcome": "passed", "screens": 6},
        {"name": "vercel_preflight", "command": "python3 scripts/vercel_preflight.py", "outcome": "passed"},
        {"name": "http_smoke_1_3_0", "command": "python3 scripts/http_smoke.py", "outcome": "blocked", "reason": "FastAPI and Uvicorn unavailable in build sandbox"},
        {"name": "live_gemini", "outcome": "not_run", "reason": "no credential or explicit opt-in"},
        {"name": "docker", "outcome": "not_run", "reason": "Docker unavailable"},
        {"name": "cloud_deployment", "outcome": "not_run", "reason": "gcloud and credentials unavailable"},
        {"name": "release_validation", "command": "python3 scripts/validate_release.py /data/food-bank-recall-closure-agent.zip", "outcome": "passed" if args.release_validated else "pending"},
    ]
    manifest = {
        "schema_version": 3,
        "project": "food-bank-recall-closure-agent",
        "version": VERSION,
        "build_timestamp": now.isoformat(timespec="seconds"),
        "git_commit": git_commit(),
        "release_status": "LOCALLY_VALIDATED" if args.release_validated else "CANDIDATE",
        "selected_model": "gemini-3.7-flash",
        "selected_adk_version": "2.7.1",
        "selected_genai_sdk_version": "2.20.0",
        "selected_fastapi_version": "0.139.2",
        "selected_pydantic_version": "2.13.4",
        "selected_starlette_version": "1.3.1",
        "selected_uvicorn_version": "0.51.0",
        "dependency_constraint_source": "Google ADK v2.7.1 official Python 3.12 constraints",
        "python": {"target": "3.12", "build_runtime": platform.python_version()},
        "entrypoints": {
            "web": "app.main:app",
            "adk": "agent:root_agent",
            "offline_golden_path": "scripts/run_golden_path.py",
            "offline_preview": "scripts/offline_preview_server.py",
            "local_configuration": "scripts/configure_local_env.py",
            "cloud_configuration_collector": "scripts/gcp_collect_config.py",
            "evidence_verifier": "scripts/verify_evidence_pack.py",
            "windows_setup": "scripts/setup_windows.cmd",
            "windows_run": "scripts/run_windows.cmd",
            "vercel": "app.main:app",
            "vercel_preflight": "scripts/vercel_preflight.py",
            "runtime_smoke": "scripts/http_smoke.py",
        },
        "executed_commands": commands,
        "docker_outcome": "NOT_RUN_DOCKER_UNAVAILABLE",
        "deployment_outcome": "NOT_RUN_GCLOUD_AND_CREDENTIALS_UNAVAILABLE",
        "vercel_outcome": "SOURCE_READY_NOT_DEPLOYED_NO_ACCOUNT_AUTH",
        "known_limitations": [
            "The 1.3.0 FastAPI/ADK real-server smoke was not executable in the dependency-limited build sandbox",
            "No live Gemini request, Docker build, Google Cloud deployment, GitHub push, or Vercel deployment occurred",
            "Google Cloud Free Tier requires billing and does not guarantee a zero invoice",
            "Evidence packs are integrity-checked but unsigned",
            "Demo administrator authentication requires replacement before production",
        ],
        "file_hash_scope": "Every release file except this self-referential release_manifest.json",
        "files": release_files(),
    }
    (ROOT / "release_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
