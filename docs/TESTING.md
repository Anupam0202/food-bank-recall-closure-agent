# Testing

## Strategy

- **Domain:** normalization, exact/partial/semantic/no-match classification, legal state map, closure blockers.
- **Safety:** disposal rejection, exact-item hold requirement, human acknowledgement, package evidence review-only rule.
- **Reliability:** idempotency keys, stable child IDs, duplicate replay, bounded model retry, poisoned Pub/Sub payloads.
- **Security:** authorization/CSRF, MIME+extension+signature/parser, byte and image limits.
- **Adapters:** Firestore hydration without cloud access, fixed-domain openFDA URL, status payload.
- **Runtime contract:** required route declarations; FastAPI health, dashboard HTML rendering, and ADK construction when dependencies are installed.
- **Golden path:** seed, process, hold/review/control, tasks, duplicate, resolution, acknowledgements, internal operational closure.

## Offline-supported commands

```bash
python -m compileall -q app tests scripts
python -m unittest discover -s tests -v
python scripts/run_golden_path.py
python scripts/check_repo.py
```

## Connected CI commands

```bash
pip install -r requirements-dev.txt
python scripts/check_dependency_compatibility.py
python -m pip check
python scripts/adk_import_smoke.py
python scripts/http_smoke.py
ruff check .
pytest -q --cov=app --cov-report=term-missing
```

## Windows Command Prompt

```bat
scripts\setup_windows.cmd
.venv\Scripts\python.exe -m unittest discover -s tests -v
scripts\run_windows.cmd
```

The Windows setup script uses `py -3.12` or the installed CPython executable directly and does not depend on POSIX activation commands. It also runs the full unit suite and a temporary real-server smoke test against both `/healthz` and `/`, preventing a successful setup result when dashboard rendering fails.

Coverage is configured for `app`; no percentage is claimed until pytest-cov actually runs. The target for domain, matching, workflow, and security is at least 80%.

## Live opt-in

```bash
RUN_LIVE_GEMINI_TESTS=1 AI_MODE=live GEMINI_API_KEY='...' python scripts/live_gemini_smoke.py
```

Tests never call Gemini by default. A missing dependency or credential is reported as skipped/blocked, not passed.

## v1.2 regression contracts

- Evidence-pack tests validate every member digest, root calculation, audit-chain linkage, final/provisional labeling, raw-payload exclusion, and unsigned-authenticity disclosure.
- Readiness tests check 0%/100% cloud profiles, regional free-tier disclosure, and absence of credential values.
- Configuration tests prove environment variables are evaluated when `Settings()` is created rather than frozen at module definition.
- Visual QA covers desktop/mobile dashboard and readiness screens, incident closure gates, and partner tasks. Browser checks reject JavaScript console errors and horizontal overflow.
