# Security and Safety

## Safety invariants

1. Only exact normalized UPC plus applicable lot/batch equality creates an automatic reversible quarantine hold.
2. Partial, semantic, image-only, or model-only evidence is always a potential match requiring human review.
3. The application never authorizes food disposal, publishes an alert, makes a medical decision, or determines product safety.
4. Every potential match must have a human resolution and every actioned partner task must have partner acknowledgement before internal operational closure.
5. `INTERNAL_CLOSED` does not change or describe official FDA/USDA status.
6. `MOCK_GEMINI`, `REPLAY`, and `LIVE_GEMINI` are visibly distinct.

## Threat model

| Threat | Control |
|---|---|
| Prompt injection in source text/image | Untrusted-data prompts, raw payload isolation, Pydantic schemas, sanitized ADK context, proposal-only tools, deterministic writes |
| Model hallucinates identifiers | Missing/ambiguous schema values; exact policy checks normalized source identifiers independently |
| Model requests disposal/safety claim | Tool allowlist, prohibited-action output, `UnsafeActionError`, audited rejection |
| Pub/Sub spoofing | Google-signed OIDC bearer validation against configured audience plus `roles/run.invoker` push account |
| Pub/Sub redelivery | Transactional incident reservation and stable child IDs |
| Poison message loop | Terminal hash-only incident and HTTP acknowledgement after sanitized audit record |
| Malicious upload | MIME+extension+magic validation, safe parser, UTF-8/JSON checks, image format/dimension/decompression limits, random object names |
| Path traversal | Original filename is never used as a path; generated object name retains only allowlisted suffix |
| SSRF | No arbitrary fetch tool; source URLs are provenance only; openFDA importer constructs a fixed `api.fda.gov` URL |
| Guest changes state | Signed HttpOnly same-site session, constant-time token check, CSRF on mutations |
| XSS/clickjacking | Jinja autoescaping, local assets, CSP, `nosniff`, frame denial, referrer/permissions policy |
| Secret disclosure | Secret Manager bindings, `.env`/credential exclusions, structured logs omit values/binaries, repository scan |
| Public evidence | Uniform bucket access, public-access prevention, private `gs://` references; no public ACL |
| Over-privileged runtime | Dedicated service account with datastore user, log writer, bucket object-user, and per-secret accessor |

## Authorization

Read-only pages and sanitized exports may be visible to a judge. Reset, upload, import, retry, acknowledgement, evidence, review resolution, and other mutations require a demo-administrator session plus CSRF. The demo token is not a substitute for production identity; production startup rejects the default.

The Pub/Sub route does not use the browser session. Production requires `PUBSUB_VERIFICATION_AUDIENCE` and verifies the Google OIDC token. Cloud Run IAM separately grants the push service account `roles/run.invoker`.

## Upload policy

Accepted documents: PDF, JSON, UTF-8 text. Accepted images: PNG, JPEG, WebP. Archives, executables, SVG, HTML, MIME/extension mismatches, malformed images, encrypted/empty/over-100-page PDFs, oversized files, and images above 6000 × 6000 are rejected. Original bytes are stored under a random name; raw binary content is not logged.

## Logging and retention

Logs contain correlation/incident ID, route/tool, state before/after, duration, result, retries, and sanitized error category. They exclude API keys, session values, raw binaries, full sensitive payloads, and hidden reasoning.

Firestore export, object lifecycle, incident retention, legal hold, and deletion periods must be set to organization policy before real use. The checked-in cleanup script intentionally retains Firestore and secrets unless an operator separately governs them.

## Remaining production work

Replace the demo token with organization identity and agency-scoped authorization; add malware scanning for arbitrary external uploads; conduct food-safety, privacy, accessibility, retention, and incident-response reviews; validate matching thresholds against historical cases.

## Portable evidence controls

- Both JSON and ZIP incident exports require an administrator session and return `Cache-Control: no-store`.
- Evidence packs recursively suppress known secret-bearing keys and exclude original source payloads and task media.
- The ZIP includes canonical records, member SHA-256 digests, and an ordered audit-event chain.
- The manifest is intentionally labeled unsigned. Self-contained hashes prove internal consistency, not signer identity; preserve the response root in a separately trusted audit system for authenticity.
- The readiness endpoint exposes booleans and safe labels only, never API keys, session secrets, administrator tokens, or secret versions.
