# Build Report

Generated: `2026-09-01T06:48:52+05:30`  
Version: `1.3.0`  
Deadline status: `after_deadline` (-4732 seconds relative to the recorded hackathon deadline)

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
| `python3 scripts/validate_release.py /data/food-bank-recall-closure-agent.zip` | PENDING |
| Clean extracted-copy compile, unit, golden-path, repository, and ZIP validation | PENDING |

## Final visual evidence

| File | Dimensions | SHA-256 |
|---|---:|---|
| `docs/screenshots/dashboard-desktop.png` | 1440 × 2098 | `22137f0990df0d809eb658a6112ca1d50fc738e032af9010ee32581bcc05c5d7` |
| `docs/screenshots/dashboard-mobile.png` | 390 × 4286 | `148d10b1a45a8a40e3451f84bbe1b13622bcd056a5a96eeedef9ee3842cebd7b` |
| `docs/screenshots/incident-desktop.png` | 1440 × 3560 | `d6a4092d2755eba159c844546c36f4ece0d0a9544763bf2e06d08e7c96823dac` |
| `docs/screenshots/partner-tasks-desktop.png` | 1440 × 1564 | `3dfff32a430cfc31783aefdd68228feebad33407071dbae546709faf3bc0b0b8` |
| `docs/screenshots/readiness-desktop.png` | 1440 × 2038 | `4a1aef7f0b867cce71a46beee018c12442c0e3b0b2145f1f37f92833b7ff85c0` |
| `docs/screenshots/readiness-mobile.png` | 390 × 3809 | `6eeee95e375b8ba509512f98bd4b02bc95e8bc80c7af387d7b989e21e66a923a` |

## Explicit limitations

- Google Cloud Free Tier requires an active billing account and can charge overages; budget alerts do not cap spend.
- The evidence-pack manifest is unsigned. Its hashes prove self-consistency; signer authenticity requires comparing the root with a separately trusted record.
- No `1.3.0` live Gemini request, Docker build, or Google Cloud deployment was claimed.
- Administrator-token authentication must be replaced by organization identity and agency-scoped authorization before real production use.
- Legal, privacy, retention, accessibility, and real historical matching validation remain organization responsibilities.
