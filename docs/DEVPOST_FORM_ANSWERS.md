# Devpost Form Answers

Copy these values into Devpost. Items marked **Confirm** depend on the entrant or on URLs created after deployment; do not invent them.

## General information

### Project name — 47/60 characters

RecallReady — Food-Bank Recall Closure Agent

### Elevator pitch — under 200 characters

An ADK agent that turns food-recall notices into traceable inventory holds, partner tasks, acknowledgements, and a verifiable closure evidence pack.

## Project story

### Inspiration

Food recalls are time-critical, but community food banks often operate across a patchwork of spreadsheets, donated inventory, package photos, and partner pantries. Receiving the notice is only the beginning. The difficult part is proving which stock was checked, which items were held, who was contacted, what each partner acknowledged, and whether any uncertainty remains. We built RecallReady to close that operational gap without pretending that an AI model can make food-safety or regulatory decisions.

### What it does

RecallReady converts a PDF, JSON record, text notice, optional openFDA record, or authenticated Pub/Sub event into a complete internal response workflow. Gemini extracts schema-constrained recall fields. Deterministic policy compares normalized UPC and lot identifiers. An exact identifier match creates a reversible quarantine hold; partial, semantic, visual, or missing-data evidence creates human-review work instead.

A real Google ADK root agent named `RecallCoordinatorAgent` uses eight typed tools to inspect sanitized workflow state, propose actions, summarize discrepancies, and surface open work. It cannot arbitrarily write status, declare food safe, authorize disposal, or claim regulator closure. The system creates partner tasks, records acknowledgements and evidence, applies closure blockers, suppresses duplicate deliveries, and produces an administrator-only evidence ZIP with a hash manifest and chain of custody.

### How we built it

The application is a Python 3.12 modular monolith using FastAPI, Jinja2, Pydantic, Google ADK 2.7.1, the Google Gen AI SDK, and Gemini 3.7 Flash. The canonical deployment is one Cloud Run service. Firestore supplies durable state and transactional idempotency, Pub/Sub supplies authenticated at-least-once event delivery with retry/dead-letter handling, private Cloud Storage holds media, and Secret Manager supplies runtime secrets.

The agent and deterministic workflow deliberately have different responsibilities. Gemini and ADK interpret messy source material and propose bounded next actions. Domain services remain the write authority for holds, task creation, acknowledgement, review resolution, and internal closure. Stable incident, match, and task identifiers make retries safe.

A Vercel FastAPI deployment profile is also included as a convenient non-commercial public judge preview. It is explicitly labeled as ephemeral when configured without Firestore and does not replace the required Google Cloud deployment proof.

### Challenges we ran into

The hardest design problem was separating useful model reasoning from operational authorization. A visually similar package can be valuable evidence, but it must not become an automatic quarantine or disposal decision. We solved this with a deterministic-first matching matrix and explicit human-review states.

A second challenge was truthful proof. Pub/Sub is at-least-once rather than exactly-once end to end, serverless filesystems are ephemeral, and a hash manifest is not automatically a digital signature. The application states those limits directly, reserves idempotency keys transactionally, labels evidence packs as unsigned, and distinguishes internal operational closure from official regulator closure.

We also repaired dependency and framework drift discovered through real Windows execution. Google ADK 2.7.1 required a newer FastAPI range, and Starlette 1.3 changed the template-response calling convention. Compatibility tests and semantic HTTP smoke checks now protect both contracts.

### Accomplishments that we're proud of

- One real ADK coordinator with exactly eight typed, bounded tools.
- A complete source-to-closure workflow instead of a chatbot response.
- Reversible exact-match holds and mandatory review for ambiguity.
- Transaction-safe duplicate suppression and stable child identifiers.
- Partner acknowledgements, deterministic closure blockers, and an auditable timeline.
- Privacy-minimized evidence packs with member hashes, audit-chain linkage, and a standalone verifier.
- Reproducible Windows setup, deterministic fixtures, 92 automated tests, clean-release validation, and responsive visual QA.
- A redacted readiness center that distinguishes local, Vercel preview, and Google Cloud production states without exposing secrets.

### What we learned

Trustworthy autonomy is not unlimited model authority. It is a controlled collaboration between probabilistic interpretation and deterministic policy. The most useful agent makes uncertainty visible, creates accountable work, survives retries, and proves completion. We also learned that deployment evidence is part of the product: judges and operators need to see the model mode, persistence layer, cloud revision, correlation IDs, and limits—not just a polished interface.

### What's next for RecallReady

Next steps are organization identity and agency-scoped authorization, malware scanning and retention policy, warehouse-system connectors, a historical-case evaluation set, digitally signed evidence roots, and pilots with food-safety and food-bank operations professionals. We would also add secure Vercel-to-Google Cloud Workload Identity Federation for teams that need the optional preview to use durable Google Cloud services without long-lived keys.

## Built with tags

Use these tags, up to the form's limit:

- Python
- FastAPI
- Jinja2
- Pydantic
- Google ADK
- Google GenAI SDK
- Gemini 3.7 Flash
- Google Cloud Run
- Firestore
- Pub/Sub
- Cloud Storage
- Secret Manager
- Cloud Build
- Vercel
- GitHub Actions
- openFDA

## Additional information

| Devpost field | Answer |
|---|---|
| Sponsor / Special Prize | Do not select Startup Excellence unless submitting for a legally incorporated organization with a corporate email. |
| Submitter Type | `Individuals` if submitting alone; otherwise select the truthful team/organization option. **Confirm.** |
| Country of residence | `India` only if this is the entrant's actual country of residence. **Confirm.** |
| Category | `Taskmaster` |
| Organization name | `N/A — individual submission`, unless submitting for an organization. **Confirm.** |
| Project start date | `08-31-26` if that is the true first project date; otherwise enter the actual date within the submission period. **Confirm.** |
| Code repository | `https://github.com/GITHUB-USERNAME/food-bank-recall-closure-agent` after push. |
| Reproducible testing in README | `Yes` |
| Hosted project | Paste the final Vercel URL for easy access; use the Cloud Run URL in the video as mandatory Google Cloud proof. |
| Google SDK | Select `Agent Development Kit (ADK)` and `Google GenAI SDK (google-genai)`. |
| Google Cloud services | After real deployment, select `Cloud Run`, `Firestore`, and `Pub/Sub`. Do not select services that were not actually deployed. |
| Architecture diagram | Upload `docs/architecture-diagram.png`. |
| Startup organization and email | Leave blank unless the eligibility requirements are genuinely met. |
| Google AI models | `Gemini 3.7 Flash`. Do not list bonus models that are not genuinely integrated and demonstrated. |
| Bonus content link | Paste a public YouTube/blog/podcast link only after publishing it with the required hackathon-entry disclosure. |
| Social link | Paste a public post only after publishing it with `#AllThingsAgentic`. |

## Judge-only testing instructions

1. Open the hosted URL. The page displays whether the run is `LIVE_GEMINI`, `MOCK_GEMINI`, or `REPLAY`.
2. Open `/healthz` and `/api/readiness` to see the deployment target, revision, persistence mode, and redacted readiness status.
3. Select **Admin** and enter the private demo token supplied in this judge-only field.
4. Select **Run seeded demonstration** once.
5. Open the generated incident. Compare the exact UPC+lot hold, ambiguous review, unchanged control inventory, partner tasks, and audit events.
6. Resolve the review and acknowledge both partner tasks. Confirm the state becomes `INTERNAL_CLOSED` only after all deterministic blockers clear.
7. Download the evidence pack and run `python scripts/verify_evidence_pack.py DOWNLOADED-FILE.zip`.
8. Replay the seeded event and confirm duplicate suppression without duplicate holds or tasks.

For source verification:

```bash
python -m unittest discover -s tests -v
python scripts/run_golden_path.py
python scripts/check_dependency_compatibility.py
python scripts/check_repo.py
```

Do not place the administrator token in the public project story, repository, screenshots, or video. Put it only in Devpost's private testing-instructions field.
