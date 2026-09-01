# Operations Runbook

## Deployment

1. Create `gemini-api-key`, `session-secret`, and `demo-admin-token` in Secret Manager. Generate random values outside source control, for example `python -c "import secrets; print(secrets.token_urlsafe(48))"`.
2. Export `GOOGLE_CLOUD_PROJECT` and optionally `GOOGLE_CLOUD_REGION`.
3. Run `bash infra/deploy_cloud_run.sh`.
4. Record the emitted revision and URL only after the smoke test passes.

The deployment script is idempotent: it enables APIs, reuses Artifact Registry/service accounts/Firestore/bucket/topics, submits a build, deploys privately, sets the real service URL as Pub/Sub OIDC audience, optionally grants public read access, creates authenticated push+DLQ, and calls `/healthz`.

## IAM

| Principal | Scope | Role | Reason |
|---|---|---|---|
| Runtime service account | project | `roles/datastore.user` | Firestore application documents |
| Runtime service account | project | `roles/logging.logWriter` | Structured application logs |
| Runtime service account | evidence bucket | `roles/storage.objectUser` | Private object create/read/delete |
| Runtime service account | each named secret | `roles/secretmanager.secretAccessor` | Runtime secret versions |
| Pub/Sub push account | Cloud Run service | `roles/run.invoker` | Authenticated push requests |
| Pub/Sub service agent | DLQ topic | `roles/pubsub.publisher` | Forward undeliverable messages |
| Pub/Sub service agent | source subscription | `roles/pubsub.subscriber` | Track dead-letter delivery attempts |

No Owner or Editor grant is required.

## Health and status

`GET /healthz` reports mode, model, repository, media, Pub/Sub flag, and revision. `GET /api/system-status` returns the same sanitized payload. A public health check does not expose secrets.

## Recall incident operations

1. Verify the source URL/limitation against the current official notice.
2. Inspect exact identifier evidence before lifting any quarantine hold.
3. Resolve each potential match through a named human review.
4. Obtain partner acknowledgement for every actioned task.
5. Attach private evidence where policy permits.
6. Export/print the incident timeline.
7. Follow organization/regulator guidance outside the app for disposition. The app never authorizes disposal.

## Pub/Sub failures

- `2xx`: message is acknowledged, including durable terminal poison records.
- `503`: retryable checkpoint is durable; Pub/Sub redelivers with exponential backoff.
- Stable idempotency and child IDs suppress duplicate actions.
- After approximately five delivery attempts, messages route to the dead-letter topic.
- Correlate logs by incident/correlation ID; do not copy raw payloads into tickets.

## Rollback

```bash
gcloud run revisions list --service recall-closure-agent --region "$GOOGLE_CLOUD_REGION"
bash infra/rollback.sh REVISION_NAME
bash infra/smoke_test.sh SERVICE_URL
```

## Secret rotation

Add a Secret Manager version, update the Cloud Run revision reference, verify health/login/live smoke, then disable the old version. Never print secret values into build logs.

## Backup and retention

Configure scheduled Firestore exports and Cloud Storage lifecycle/retention under organization policy. Keep evidence private. The app returns private URIs; add authenticated proxy or short-lived signed URL issuance only after identity policy is defined.

## Cleanup

```bash
CONFIRM_CLEANUP=DELETE_RECALL_CLOSURE_RESOURCES bash infra/cleanup.sh
```

The script removes Cloud Run and Pub/Sub. It intentionally retains Firestore, secrets, and—unless separately confirmed—the evidence bucket.

## Readiness and evidence-pack operations

Open `/readiness` before any production-readiness claim. A score below 100 identifies exact missing controls without showing credentials. The `free-tier` profile is a cost posture, not a guarantee of a zero invoice.

After internal work is complete, an administrator can download the incident evidence pack and verify it offline:

```bash
python scripts/verify_evidence_pack.py incident_ID-evidence-pack.zip
```

Archive the reported pack root and ZIP digest in a separately trusted case-management or immutable log when authenticity matters. The built-in manifest is unsigned and must not be presented as a regulator signature.
