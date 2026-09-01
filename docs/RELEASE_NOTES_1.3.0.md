# Release 1.3.0 — Submission and Vercel Readiness

Release 1.3.0 adds a safe Vercel judge-preview profile while preserving Cloud Run as the canonical Google Cloud deployment required by the hackathon.

## Added

- Official FastAPI `app.main:app` Vercel entrypoint, Python 3.12 pin, Function limits, and bundle exclusions.
- Fail-closed hosted `demo` environment with HTTPS, random-secret, and 4 MB upload-limit validation.
- Ephemeral `/tmp` media path and explicit serverless/durability disclosure.
- Redacted hosted-preview readiness checks.
- Vercel preflight command and six deployment contract tests.
- GitHub repository creation and push guide for Windows.
- Copy-ready Devpost form answers and judge-only testing instructions.
- Timed, conversational 3:55 video script with Google Cloud proof early.
- Submission-ready architecture diagram PNG.

## Important boundary

A Vercel URL is useful as the optional hosted-project field, but the rules require the video to demonstrate that the backend runs on Google Cloud. Record the Cloud Run revision, `.run.app` URL, or Google Cloud logs. Do not present an ephemeral Vercel preview as durable Google Cloud execution.
