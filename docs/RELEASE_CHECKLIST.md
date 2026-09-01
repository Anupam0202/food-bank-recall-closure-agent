# Release Checklist

- [x] Domain state machine and deterministic match policy implemented.
- [x] Reproducible synthetic recall, inventory, agencies, and package images included.
- [x] Idempotent golden path reaches `INTERNAL_CLOSED` only after human actions.
- [x] Google ADK coordinator and Gemini live adapters included.
- [x] FastAPI/Jinja operations UI and authenticated mutations included.
- [x] Firestore, Pub/Sub, Cloud Storage, Secret Manager, and Cloud Run assets included.
- [x] Unit, safety, smoke, syntax, template, repository, and visual checks run locally.
- [x] Source limitations and internal-closure semantics visible in code, UI, and docs.
- [ ] Production dependency import smoke — blocked in the offline build sandbox.
- [ ] Docker build — not run because Docker is unavailable in the build sandbox.
- [ ] Live Gemini/ADK execution — not run because package installation and credentials are unavailable.
- [ ] Cloud Run deployment — not run because cloud credentials are unavailable.

The unchecked items are explicit external validation steps, not claims of success. CI and deployment commands are checked in for a connected environment.
