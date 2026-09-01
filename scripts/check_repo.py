#!/usr/bin/env python3
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXCLUDE_DIRS = {".git", ".venv", "__pycache__", "release-validation", "runtime"}
TEXT_EXT = {".py", ".md", ".txt", ".toml", ".yaml", ".yml", ".json", ".html", ".css", ".js", ".sh", ".cmd", ""}
forbidden_markers = ["FIXME", "CHANGEME", "PLACEHOLDER IMPLEMENTATION", "pass  # TODO"]
secret_patterns = [
    re.compile(r"AIza[0-9A-Za-z_-]{30,}"),
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    re.compile(r"(?i)gemini_api_key\s*=\s*['\"][^'\"]{12,}['\"]"),
]
issues = []
for path in ROOT.rglob("*"):
    if not path.is_file() or any(part in EXCLUDE_DIRS for part in path.parts) or path.suffix not in TEXT_EXT:
        continue
    text = path.read_text(encoding="utf-8", errors="ignore")
    if path.name != "check_repo.py":
        for marker in forbidden_markers:
            if marker in text:
                issues.append(f"{path.relative_to(ROOT)}: forbidden marker {marker}")
    if path.name != ".env.example":
        for pattern in secret_patterns:
            if pattern.search(text):
                issues.append(f"{path.relative_to(ROOT)}: possible embedded secret")
if issues:
    print("Repository check FAILED")
    print("\n".join(f"- {issue}" for issue in issues))
    raise SystemExit(1)
required = ["README.md", "Dockerfile", "agent.py", "app/main.py", "docs/ARCHITECTURE.md", "docs/ARCHITECTURE_DECISIONS.md", "docs/SECURITY.md", "docs/DEVPOST_SUBMISSION.md", "tests/test_workflow.py", "tests/test_dependency_contract.py", "app/agents/prompts.py", "app/agents/output_schemas.py", "app/workflows/idempotency.py", "constraints-python312.txt", "scripts/setup_windows.cmd", "scripts/run_windows.cmd", "scripts/check_dependency_compatibility.py", "app/services/evidence_pack_service.py", "app/services/readiness_service.py", "app/templates/readiness.html", "docs/GOOGLE_CLOUD_FREE_SETUP.md", "docs/UPGRADE_SCORECARD.md", "scripts/configure_local_env.py", "scripts/gcp_collect_config.py", "scripts/verify_evidence_pack.py", "docs/screenshots/readiness-desktop.png", "docs/screenshots/readiness-mobile.png", "vercel.json", ".python-version", ".vercelignore", "scripts/vercel_preflight.py", "tests/test_vercel_deployment.py", "docs/GITHUB_VERCEL_DEPLOYMENT.md", "docs/DEVPOST_FORM_ANSWERS.md", "docs/VIDEO_PITCH_4_MIN.md", "docs/SUBMISSION_CHECKLIST.md", "docs/RELEASE_NOTES_1.3.0.md", "docs/architecture-diagram.png"]
missing = [p for p in required if not (ROOT / p).exists()]
if missing:
    raise SystemExit(f"Missing required files: {missing}")
print("Repository check PASS: no placeholders, obvious secrets, or required-file gaps")
