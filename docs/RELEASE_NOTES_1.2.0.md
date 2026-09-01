# Release 1.2.0 — Proof and Readiness

## User-verified baseline

- 75 tests ran successfully on Windows with one environment-specific skip.
- FastAPI served `/`, `/login`, `/about`, `/inventory`, `/partner/tasks`, the golden-path API, and an incident page with HTTP 200 responses.
- The seeded workflow created a reversible exact hold, routed ambiguity to human review, created partner tasks, and suppressed duplicate source work.

## Corrected

- Fixed the HTTP smoke test's false negative. Version 1.1.2 looked for the marketing string `Food-Bank Recall Closure Operations`, while the actual rendered title was `Operations dashboard · Recall Closure`. Version 1.2.0 verifies a stable `data-app-id`, the real dashboard heading, MIME types, and `/api/readiness`.
- Environment settings now evaluate at `Settings()` construction time and load a local `.env` when `python-dotenv` is installed.
- Production validation now requires HTTPS base and Pub/Sub audience URLs.

## Added

- Administrator-only tamper-evident incident evidence-pack ZIP export.
- Per-file SHA-256 manifest and sequential audit-event hash chain.
- Raw uploads/task media excluded from portable evidence packs by design.
- Redacted `/readiness` UI and `/api/readiness` endpoint.
- Cross-platform local `.env` generator with hidden Gemini-key entry.
- Read-only Google Cloud identifier/resource collector.
- Comprehensive no-surprise-cost Google Cloud setup and teardown guide.
- Cloud Run scale-to-zero and one-instance default cost safeguards.
- Upgrade scorecard tied to the published hackathon weighting.

## Safety boundary

Internal closure remains an organization workflow state. It does not declare product safety, authorize disposal, publish alerts, or change FDA/USDA recall status.
