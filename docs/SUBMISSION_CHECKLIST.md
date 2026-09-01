# Final Submission Checklist

## Repository

- [ ] Public GitHub URL opens without authentication, or both judge accounts have private access.
- [ ] Default branch is `main` and the latest commit contains release 1.3.0.
- [ ] `.env`, API keys, tokens, service-account files, runtime uploads, and ZIPs are absent.
- [ ] README setup, tests, Cloud Run deployment, Vercel preview, and architecture diagram render correctly.

## Deployments

- [ ] Cloud Run deployment is real and `/healthz` returns `200`.
- [ ] Firestore, Pub/Sub, and the Cloud Run revision are visible for recording.
- [ ] `LIVE_GEMINI` appears only after a real successful Gemini configuration.
- [ ] Optional Vercel preview returns `200` and `/api/readiness` reports `deployment_target: vercel`.
- [ ] Vercel administrator token is stored only in the private Devpost testing field.

## Devpost

- [ ] Project name and elevator pitch fit the form limits.
- [ ] Submitter type, residence, organization status, and start date are personally confirmed.
- [ ] Category is Taskmaster.
- [ ] ADK and Google GenAI SDK are selected.
- [ ] Cloud Run, Firestore, and Pub/Sub are selected only after real use.
- [ ] `docs/architecture-diagram.png` is uploaded and under 35 MB.
- [ ] Repository and hosted URLs are pasted and opened in a private browser window.
- [ ] Reproducible testing answer is Yes.

## Video

- [ ] Public YouTube or Vimeo URL works without sign-in and is not unlisted.
- [ ] Duration is 3:55 or less.
- [ ] Google Cloud proof appears in the first 35 seconds.
- [ ] One unedited live action sequence shows source → hold/review → tasks → closure.
- [ ] No credentials or private evidence appear.
- [ ] The spoken mode matches the displayed `LIVE_GEMINI`, `MOCK_GEMINI`, or `REPLAY` badge.

## Optional bonus

- [ ] Public content explicitly says it was created for entry into the All Things Agentic Hackathon.
- [ ] Social post includes `#AllThingsAgentic`.
- [ ] Startup Excellence is selected only for an incorporated organization with a corporate email.
