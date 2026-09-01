# Four-Minute Demonstration Script

**0:00–0:15 — Show the outcome first.** Open the seeded dashboard. “This turns a recall source record into verified internal action across partner pantries.” Point to one quarantine hold, one human-review item, two partner tasks, the `MOCK_GEMINI`/`LIVE_GEMINI` badge, and the disclaimer.

**0:15–0:45 — Trigger.** Sign in and click **Run seeded demonstration**. Open the incident. Show the synthetic source label, hash/provenance, and `gemini-3.7-flash` configuration. State clearly whether this run is mock or live.

**0:45–1:30 — Extraction and matching.** Show structured recall fields. In the evidence ledger, contrast:

- exact normalized UPC+lot → reversible quarantine hold;
- same UPC but missing lot → potential match requiring human review;
- unrelated control → unchanged.

Say: “Gemini interprets; deterministic policy authorizes.”

**1:30–2:10 — ADK agentic loop.** Show the `ADK_COORDINATOR` audit event and explain that one real ADK root agent receives sanitized context and has eight typed read/proposal tools. It cannot write arbitrary status or authorize disposal.

**2:10–2:50 — Human completion.** Upload optional task evidence, resolve the potential match as inspected, and submit both partner acknowledgements. Refresh and show `VERIFIED` then `INTERNAL_CLOSED` in the timeline. Say: “This is internal operational closure, not FDA/USDA closure.”

**2:50–3:15 — Idempotency.** Run `python scripts/run_golden_path.py` or replay the event. Show `duplicate_suppressed: true`, unchanged task count, and a `DUPLICATE_EVENT` record.

**3:15–3:42 — Google Cloud readiness.** Show Cloud Run container, Firestore transaction/stable IDs, authenticated Pub/Sub push with five-attempt DLQ, private Storage, Secret Manager, JSON logs, and CI. Do not claim deployment unless a real URL and smoke exist.

**3:42–3:55 — Close.** “The agent does not merely detect a recall. It coordinates, verifies, and proves the organization’s internal response while keeping safety decisions accountable.” Stop before 4:00.

## v1.2 proof moments

- Open `/readiness` and show that secret values are never rendered.
- On an incident, explain the deterministic closure blockers.
- Download the administrator evidence pack; show `manifest.json`, `SHA256SUMS.txt`, and `chain-of-custody.json` without displaying private media.
- In Google Cloud, show `min-instances=0`, `max-instances=1`, the Cloud Run revision, and the matching `/healthz` response.
