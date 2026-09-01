# Four-Minute Video Pitch

Record one continuous take at 1080p. Keep the browser zoom near 100%, notifications disabled, and the Cloud Run `.run.app` hostname or Cloud Console visible during the proof segment. Vercel is optional convenience hosting; it is not a substitute for Google Cloud proof.

## 0:00–0:18 — Human problem and outcome

**Screen:** Cloud Run-hosted dashboard with a completed seeded incident visible.

**Say:** “A food recall alert is not the finish line. A food bank still has to locate donated stock, coordinate partner pantries, resolve uncertainty, and prove every action was completed. RecallReady turns that messy process into one traceable workflow.”

## 0:18–0:35 — Prove Google Cloud immediately

**Screen:** Show the `.run.app` URL, then the matching Cloud Run service and revision in Google Cloud Console.

**Say:** “This is the live FastAPI backend on Google Cloud Run. The same revision uses Firestore for durable workflow state, Pub/Sub for authenticated event delivery, private Cloud Storage for evidence, and Secret Manager for credentials.”

## 0:35–1:03 — Trigger the live workflow

**Screen:** Return to the dashboard. Show the `LIVE_GEMINI · gemini-3.7-flash` badge. Sign in and select **Run seeded demonstration**.

**Say:** “I’ll run a fictional but fully reproducible recall drill. Gemini extracts structured fields from the source, and our Google ADK coordinator starts the operational workflow. The interface always discloses whether Gemini is live, mocked, or replayed.”

## 1:03–1:43 — Show safe action, not chat

**Screen:** Open the incident and point to the three inventory outcomes.

**Say:** “This item has an exact normalized UPC and lot, so deterministic policy creates a reversible quarantine hold. This second item shares partial evidence but lacks the recalled lot, so it becomes human review. And this unrelated control remains untouched. Gemini interprets; deterministic policy authorizes.”

## 1:43–2:14 — Show the real ADK role

**Screen:** Show the `ADK_COORDINATOR` audit event and the architecture diagram briefly.

**Say:** “One real ADK root agent, RecallCoordinatorAgent, uses eight typed tools to inspect sanitized state, propose actions, and summarize open work. It cannot declare food safe, authorize disposal, or write arbitrary statuses. That boundary makes the automation useful without making it reckless.”

## 2:14–2:55 — Complete the loop

**Screen:** Resolve the ambiguous match, acknowledge both partner tasks, and refresh the incident timeline.

**Say:** “Now I record the inspection result and both partner acknowledgements. Closure is not generated text—it is a state-machine decision. Only after every review and partner task clears does the incident become internally closed. That means our operational response is complete; it never claims the regulator closed the recall.”

## 2:55–3:22 — Prove the work

**Screen:** Download the evidence pack and briefly show `manifest.json`, `chain-of-custody.json`, and `SHA256SUMS.txt`.

**Say:** “The agent produces a privacy-minimized evidence pack with source provenance, inventory decisions, partner tasks, ordered audit events, closure status, and verifiable SHA-256 hashes. The pack explicitly says it is unsigned, so integrity is never misrepresented as signer authenticity.”

## 3:22–3:40 — Retry safety

**Screen:** Replay the same event or show the duplicate audit record and unchanged task count.

**Say:** “Pub/Sub is at-least-once, so retries are expected. Stable incident and task identifiers suppress this duplicate without repeating holds or partner work.”

## 3:40–3:55 — Close

**Screen:** Architecture diagram, then dashboard outcome.

**Say:** “RecallReady does not just detect a recall. It coordinates action, keeps uncertain decisions accountable, and proves the internal response reached closure. That is a Taskmaster agent doing the work—not merely describing it.”

Stop recording by `3:55` to retain a five-second safety margin.

## Recording checklist

- Show a real Cloud Run revision or `.run.app` URL.
- Show `LIVE_GEMINI` only when a real call is configured and succeeds.
- Keep the run unedited during the proof-of-action sequence.
- Never reveal the Gemini key, session secret, administrator token, service-account material, or private evidence.
- Upload publicly to YouTube or Vimeo; unlisted content does not satisfy the stated public-video requirement.
