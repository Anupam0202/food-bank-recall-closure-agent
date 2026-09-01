# Google Cloud No-Surprise-Cost Setup

This guide separates **truly no-billing local use** from **Google Cloud Free Tier use**. They are not the same.

## Choose the correct path

| Path | Billing account | Google Cloud deployment | Hackathon cloud proof | Cost risk |
|---|---:|---:|---:|---|
| Local mock | Not required | No | No | None |
| Local + Gemini Developer API free tier | Not required for eligible free-tier access | No | No | Subject to Gemini free-tier availability/rate limits |
| Cloud Run + Google Cloud Free Tier | **Required** | Yes | Yes | $0 only while every service stays within its allowance |
| Hackathon/free-trial credits | Required Free Trial account | Yes | Yes | Credits absorb eligible usage until they expire/exhaust |

Google explicitly requires an active billing account to access the Google Cloud Free Tier. Budget alerts **do not cap charges**. Treat “free” as an allowance, not a spending guarantee.

## Current official allowances used by this project

Checked against official documentation on 2026-09-01:

- Cloud Run request-based billing: 2 million requests/month, 360,000 GiB-seconds memory, 180,000 vCPU-seconds, and 1 GB North America outbound transfer/month.
- Firestore: one free database/project, 1 GiB stored, 50,000 reads/day, 20,000 writes/day, 20,000 deletes/day, 10 GiB outbound/month.
- Cloud Storage: 5 GB-month, 5,000 Class A and 50,000 Class B operations/month, limited to `us-central1`, `us-east1`, and `us-west1` for the storage allowance.
- Pub/Sub: 10 GiB messages/month.
- Secret Manager: 6 active secret versions and 10,000 access operations/month.

Always re-check pricing before deployment:

- <https://docs.cloud.google.com/free/docs/free-cloud-features>
- <https://cloud.google.com/run/pricing>
- <https://cloud.google.com/firestore/pricing>
- <https://cloud.google.com/storage/pricing>
- <https://cloud.google.com/pubsub/pricing>
- <https://cloud.google.com/secret-manager/pricing>
- <https://ai.google.dev/gemini-api/docs/pricing>

## Path A — completely local and free

From Windows Command Prompt:

```bat
.venv\Scripts\python.exe scripts\configure_local_env.py --force
scripts\run_windows.cmd
```

This creates a private `.env` with generated session/admin secrets and keeps `AI_MODE=mock`, Firestore off, and Cloud Storage off. `.env` is excluded from the release and Git.

For a free-tier Gemini Developer API key while retaining all state locally:

1. Open <https://aistudio.google.com/apikey>.
2. Sign in and create/select a project eligible for Gemini Developer API free-tier access.
3. Restrict the key to the Generative Language API where available.
4. Never commit, screenshot, paste into chat, or put the key in browser JavaScript.
5. Run:

```bat
.venv\Scripts\python.exe scripts\configure_local_env.py --live --force
scripts\run_windows.cmd
```

The key prompt is hidden. The script writes it only to the Git-ignored local `.env`.

**Data warning:** the Gemini Developer API free tier can have different data-use terms from paid/enterprise services. Do not send confidential donor, client, partner, or regulated data until your organization approves the current terms. The seeded demo is entirely synthetic.

## Path B — Google Cloud deployment within free allowances

### 1. Use Google Cloud Shell

Open <https://shell.cloud.google.com/>. Cloud Shell already includes `gcloud`, Git, and a Linux shell. Upload/extract this repository or clone your private repository there.

### 2. Create/select a project and link billing

Project IDs are globally unique. Replace the sample value:

```bash
export GOOGLE_CLOUD_PROJECT='recall-closure-your-unique-suffix'
export GOOGLE_CLOUD_REGION='us-central1'
gcloud projects create "$GOOGLE_CLOUD_PROJECT" --name='Recall Closure Demo'
gcloud config set project "$GOOGLE_CLOUD_PROJECT"
```

Link the project to a Free Trial, hackathon-credit, or paid billing account in **Billing → My projects**. The project cannot use Cloud Run Free Tier without an active billing account.

To discover non-secret IDs:

```bash
gcloud auth list --filter=status:ACTIVE
gcloud config get-value project
gcloud projects describe "$GOOGLE_CLOUD_PROJECT" --format='value(projectNumber)'
gcloud billing projects describe "$GOOGLE_CLOUD_PROJECT"
```

### 3. Create the three secrets safely

Get the Gemini API key from <https://aistudio.google.com/apikey>. In Cloud Shell, input it without echoing:

```bash
read -rsp 'Gemini API key: ' GEMINI_KEY; echo
printf '%s' "$GEMINI_KEY" | gcloud secrets create gemini-api-key --data-file=-
unset GEMINI_KEY
python3 -c 'import secrets; print(secrets.token_urlsafe(48))' | gcloud secrets create session-secret --data-file=-
python3 -c 'import secrets; print(secrets.token_urlsafe(32))' | gcloud secrets create demo-admin-token --data-file=-
```

If a secret already exists, add a version instead of creating it:

```bash
printf '%s' "$VALUE" | gcloud secrets versions add SECRET_NAME --data-file=-
```

Do not print secret values into logs. The deployment mounts Secret Manager references.

### 4. Deploy with cost guardrails

```bash
export CLOUD_RUN_MAX_INSTANCES=1
export FIRESTORE_LOCATION='us-central1'
bash infra/deploy_cloud_run.sh
```

The script uses:

- request-based Cloud Run billing and scale-to-zero (`min-instances=0`);
- one maximum instance by default;
- 1 vCPU, 512 MiB, concurrency 20;
- one regional Firestore database;
- one private regional evidence bucket with public-access prevention;
- authenticated Pub/Sub OIDC push and a bounded dead-letter policy;
- three Secret Manager secrets and least-privilege runtime identities.

A one-instance cap protects cost but also caps throughput. Raise it only after reviewing load and budget.

### 5. Collect every required identifier

After deployment:

```bash
python3 scripts/gcp_collect_config.py \
  --project "$GOOGLE_CLOUD_PROJECT" \
  --region "$GOOGLE_CLOUD_REGION" \
  --write-env-template
```

The command creates a redacted `gcp-readiness.json` and a non-secret `.env.cloud.generated`. It checks the account, project number, billing link, Cloud Run URL, Firestore, bucket, Pub/Sub topic/subscription, and secret names. It never reads or writes secret values.

### 6. Environment-value map

| Variable | Obtain it from | Recommended value |
|---|---|---|
| `APP_ENV` | Fixed | `production` |
| `PORT` | Cloud Run injects it | `8080` in the container |
| `APP_BASE_URL` | `gcloud run services describe ... --format=value(status.url)` | Cloud Run HTTPS URL |
| `SESSION_SECRET` | Generated | Secret Manager `session-secret:latest` |
| `DEMO_ADMIN_TOKEN` | Generated | Secret Manager `demo-admin-token:latest` |
| `AI_MODE` | Fixed | `live` |
| `MODEL_NAME` | Gemini model documentation | `gemini-3.7-flash` |
| `GEMINI_API_KEY` | Google AI Studio | Secret Manager `gemini-api-key:latest` |
| `GOOGLE_CLOUD_PROJECT` | `gcloud config get-value project` | Your project ID |
| `GOOGLE_CLOUD_REGION` | Cost/location choice | `us-central1` |
| `FIRESTORE_DATABASE` | Created database | `(default)` |
| `USE_FIRESTORE` | Fixed for cloud | `true` |
| `GCS_BUCKET` | Deployment output/collector | `recall-closure-evidence-PROJECT_ID` |
| `USE_CLOUD_STORAGE` | Fixed for cloud | `true` |
| `PUBSUB_VERIFICATION_AUDIENCE` | Cloud Run service URL | Same HTTPS URL as `APP_BASE_URL` |
| `CLOUD_COST_PROFILE` | Fixed | `free-tier` |
| `CLOUD_RUN_MAX_INSTANCES` | Cost decision | `1` for demo |

### 7. Create alerts and hard limits

1. Open <https://console.cloud.google.com/billing/budgets>.
2. Scope the budget to only this project.
3. Choose a small amount you can afford (for example USD 1 or 5).
4. Keep alerts at 50%, 90%, and 100%, and add 1% for early warning.
5. Configure API quotas where a service supports them.
6. Remember: a budget alert is notification, **not** a cap. Automated billing disablement can stop resources but can also corrupt or interrupt workloads and can lag behind spend.

### 8. Capture hackathon proof

Show, without exposing credentials:

- Cloud Run service URL and current revision;
- `/healthz` and `/api/readiness` returning 200;
- Cloud Run request logs with a correlation ID;
- Firestore incident/match/task/audit documents;
- private bucket public-access prevention;
- Pub/Sub push subscription, OIDC service account, retry policy, and DLQ;
- Secret Manager secret **names only**;
- `min-instances=0` and `max-instances=1`;
- one duplicate replay that produces no duplicate task or hold.

Run the post-deploy checks:

```bash
SERVICE_URL="$(gcloud run services describe recall-closure-agent --region us-central1 --format='value(status.url)')"
bash infra/smoke_test.sh "$SERVICE_URL"
python3 scripts/gcp_collect_config.py --project "$GOOGLE_CLOUD_PROJECT"
```

## Teardown

When judging is complete, prevent ongoing usage:

```bash
bash infra/cleanup.sh
```

Review the console afterward for Artifact Registry images, Cloud Storage objects, Firestore data, Pub/Sub resources, and active secret versions. Deleting a project is the strongest cleanup, but it is destructive and delayed; export anything required first.
