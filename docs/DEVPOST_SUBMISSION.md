# Devpost Submission

## Category

Taskmaster

## Project summary

Food-Bank Recall Closure Operations converts a recall source record into a traceable internal response across a food bank and partner pantries. It combines Gemini interpretation, a real Google ADK coordinator, deterministic safety policy, partner acknowledgement, and an auditable closure timeline.

## Inspiration

Recall alerts can arrive quickly, but donated stock is already distributed across locations with messy identifiers and package photos. The operational gap is proving affected inventory was found and handled—not merely repeating the alert.

## Features

- PDF/JSON/text source ingestion and optional openFDA import
- provenance, original source preservation, and limitation display
- Gemini schema-constrained extraction and review-only image observation
- deterministic UPC+lot exact matching
- reversible quarantine holds and potential-match human review
- partner tasks, evidence, acknowledgement, and closure verification
- Pub/Sub redelivery idempotency and poison-message handling
- Firestore, Cloud Storage, Secret Manager, Cloud Run, CI, and JSON logs
- explicit live/mock/replay disclosure

## How it works

Gemini transforms untrusted source content into Pydantic-validated fields. The deterministic workflow compares normalized identifiers and owns all writes. Exact identifiers create a reversible hold; partial/model evidence creates review work. One ADK 2.x root agent calls eight sanitized read/proposal tools to summarize discrepancies and open actions. Humans resolve reviews and acknowledge tasks; only then can the state machine record internal operational closure.

## Technology used

Python 3.12; FastAPI; Jinja2; Pydantic 2; Google ADK 2.7.1; Google Gen AI SDK 2.20.0; Gemini 3.7 Flash; Firestore; Pub/Sub; Cloud Storage; Secret Manager; Cloud Run; Cloud Build; GitHub Actions.

## Data sources

The repeatable demo uses only fictional inventory, organizations, and Pillow-generated package images. An optional openFDA importer preserves the original record and displays the limitation that it is not an authoritative real-time public-alert or official lifecycle feed. Operators are directed to current FDA/USDA notices.

## Architecture

A modular monolith runs as one Cloud Run service. Pub/Sub or authenticated operator actions enter FastAPI. Gemini and ADK provide bounded interpretation/proposals. Firestore stores durable state and transactions; private Cloud Storage stores evidence; deterministic domain services enforce safety and closure.

## Challenges

The hardest issue was separating useful model interpretation from operational authorization. A package image can indicate similarity but cannot safely create an exact match or disposition. Pub/Sub push is at-least-once, so the workflow uses transactionally reserved incident keys and stable child IDs instead of claiming exactly-once transport.

## Findings and learning

Trustworthy autonomy means making uncertainty visible, creating accountable work, and proving completion. The most valuable agent is not the one with unrestricted writes; it is the one that interprets complexity while deterministic controls preserve safety.

## Safety

The app does not publish alerts, determine safety, authorize disposal, or close official recalls. Exact matching means a reversible internal quarantine hold. Potential matches require human review. Every actioned partner task needs acknowledgement.

## Testing instructions

```bash
python -m unittest discover -s tests -v
python scripts/run_golden_path.py
```

For a connected environment:

```bash
pip install -r requirements-dev.txt
python scripts/adk_import_smoke.py
ruff check .
pytest -q --cov=app
```

## Google Cloud proof checklist

- [ ] Cloud Run URL and revision captured after real deployment
- [ ] `/healthz` response captured
- [ ] Firestore incident/match/task/audit documents shown
- [ ] Authenticated Pub/Sub delivery and duplicate replay shown
- [ ] Private Storage object shown without public ACL
- [ ] Secret Manager references shown without secret values
- [ ] Structured Cloud Logging correlation shown

These boxes remain unchecked in the offline build because cloud deployment was not executed.

## Future work

Replace demo authentication with organization identity and agency scopes; pilot with food-safety staff; integrate warehouse systems; add malware scanning and policy-driven retention; evaluate matching on historical cases; complete external accessibility/privacy/security review.

## v1.2 judging proof

- **Operational utility:** the workflow closes the loop from source provenance to quarantine/review, partner acknowledgement, deterministic blockers, and a portable integrity pack.
- **Architectural discipline:** one ADK coordinator uses exactly eight typed tools while deterministic policy remains the write authority.
- **Demo readiness:** the readiness center exposes mode, cloud prerequisites, cost controls, and revision proof without credentials. The Google Cloud setup guide separates no-billing local use from billing-required Free Tier deployment.
