# API and Web Routes

## Read-only

| Method | Path | Purpose |
|---|---|---|
| GET | `/healthz` | Sanitized health and selected modes |
| GET | `/api/system-status` | Same mode/revision information |
| GET | `/` | Operations dashboard |
| GET | `/incidents/{incident_id}` | Incident evidence and timeline |
| GET | `/incidents/{incident_id}/print` | Print-ready incident record |
| GET | `/inventory` | Distributed inventory status |
| GET | `/partner/tasks` | Partner action queue |
| GET | `/about` | Safety and architecture explanation |
| GET | `/api/incidents/{incident_id}` | Typed incident aggregate |
| GET | `/api/incidents/{incident_id}/export.json` | JSON audit export |

## Browser-authenticated mutations

All require a signed administrator session and CSRF token.

| Method | Path | Purpose |
|---|---|---|
| POST | `/api/demo/reset` | Reset and seed fictional data |
| POST | `/api/demo/seed` | Seed fictional data |
| POST | `/api/demo/run-golden-path` | Execute deterministic demo |
| POST | `/api/recalls/upload` | Validate/store PDF/JSON/text and process |
| POST | `/api/recalls/import` | Fixed-domain, operator-initiated openFDA import |
| POST | `/api/incidents/{incident_id}/retry` | Resume a durable retryable incident |
| POST | `/api/tasks/{task_id}/acknowledge` | Record partner acknowledgement |
| POST | `/api/tasks/{task_id}/evidence` | Store private completion evidence |
| POST | `/api/matches/{match_id}/resolve` | Record human review resolution |
| POST | `/api/inventory/{item_id}/package-evidence` | Record image observation as review-only evidence |

## Service-authenticated event

`POST /pubsub/recall` verifies the configured Google OIDC audience in production. Malformed permanent payloads are hashed, recorded as terminal, and acknowledged. Transient model/workflow failures return 503 after a durable checkpoint.

Legacy `/api/recalls/ingest` and `/api/recalls/import-openfda` aliases remain hidden from OpenAPI for compatibility.

Local evidence references use an administrator-authenticated `/media/{object_name}` proxy; the directory is never mounted publicly. Production Cloud Storage objects remain private and are not exposed as public URLs.

## Readiness and exports (v1.2)

| Method | Path | Authentication | Purpose |
|---|---|---|---|
| GET | `/api/readiness` | Public, redacted | Local/cloud prerequisite checks and cost guardrails |
| GET | `/readiness` | Public, redacted | Human-readable readiness control plane |
| GET | `/api/incidents/{incident_id}/export.json` | Administrator session | Normalized incident export; `no-store` |
| GET | `/api/incidents/{incident_id}/evidence-pack.zip` | Administrator session | Privacy-minimized integrity pack with SHA-256 manifest and audit chain |

The evidence ZIP is an internal operational record, not a regulator certificate. Its manifest is unsigned; compare the returned `X-Evidence-Root-SHA256` or ZIP digest with a separately trusted log if authenticity must be demonstrated.
