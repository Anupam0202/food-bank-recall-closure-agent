# GitHub and Vercel Deployment

## Critical hackathon rule

Vercel is an optional public judge preview. It does **not** replace the required Google Cloud proof. The demonstration video must show the backend running on Google Cloud, such as a real Cloud Run dashboard, revision, logs, or `.run.app` URL. Use the supplied Cloud Run deployment as the canonical judging backend and Vercel as a convenient mirror.

## 1. Extract a clean release

Extract the ZIP into a new `food-bank-recall-closure-agent` folder. Do not merge it into an older release. Confirm that `.env`, service-account keys, and credential files are absent.

## 2. Install Git and GitHub CLI on Windows

Open Command Prompt:

```bat
winget install --id Git.Git -e
winget install --id GitHub.cli -e
```

Close and reopen Command Prompt, then authenticate in the browser:

```bat
gh auth login --web
```

Choose `GitHub.com`, `HTTPS`, and browser authentication.

## 3. Create the local history and public repository

```bat
cd C:\Users\anupa\Downloads\food-bank-recall-closure-agent
git init
git config user.name "YOUR DISPLAY NAME"
git config user.email "YOUR GITHUB EMAIL"
git add .
git status --short
git commit -m "Release 1.3.0: recall closure agent submission"
git branch -M main
gh repo create food-bank-recall-closure-agent --public --source=. --remote=origin --push
gh repo view --web
```

Before committing, verify that `.env` is ignored:

```bat
git check-ignore .env
```

The expected response is `.env`. If no response appears, stop and repair `.gitignore` before pushing.

### Manual GitHub fallback

Create an empty repository named `food-bank-recall-closure-agent` on GitHub. Do not initialize it with a README, license, or `.gitignore`. Then run:

```bat
git remote add origin https://github.com/GITHUB-USERNAME/food-bank-recall-closure-agent.git
git push -u origin main
```

## 4. Recommended Vercel path

1. Sign in to Vercel with GitHub.
2. Select **Add New → Project**.
3. Import `food-bank-recall-closure-agent`.
4. Leave Framework Preset, Root Directory, Build Command, and Output Directory on automatic/default settings. Vercel detects `app.main:app` from `pyproject.toml`.
5. Add the environment variables below for **Production**, **Preview**, and **Development** as appropriate.
6. Deploy once to obtain the `.vercel.app` hostname.
7. Set `APP_BASE_URL` to that exact HTTPS URL and redeploy.

Vercel's documented FastAPI entrypoint is `app.main:app`. The application is one Python Function with a 60-second configured maximum duration. Tests, docs, screenshots, runtime files, and credentials are excluded from the Function bundle.

## 5. Vercel environment variables

Generate two different random secrets locally:

```bat
py -3.12 -c "import secrets; print(secrets.token_urlsafe(48))"
py -3.12 -c "import secrets; print(secrets.token_urlsafe(32))"
```

Add these values in Vercel Project Settings → Environment Variables:

```dotenv
APP_ENV=demo
DEPLOYMENT_TARGET=vercel
APP_BASE_URL=https://PROJECT-NAME.vercel.app
SESSION_SECRET=PASTE-FIRST-RANDOM-VALUE
DEMO_ADMIN_TOKEN=PASTE-SECOND-RANDOM-VALUE
AI_MODE=mock
MODEL_NAME=gemini-3.7-flash
MODEL_MAX_ATTEMPTS=3
GOOGLE_CLOUD_REGION=us-central1
FIRESTORE_DATABASE=(default)
USE_FIRESTORE=false
USE_CLOUD_STORAGE=false
CLOUD_COST_PROFILE=free-tier
CLOUD_RUN_MAX_INSTANCES=1
MAX_DOCUMENT_BYTES=4000000
MAX_IMAGE_BYTES=4000000
RUNTIME_UPLOAD_DIR=/tmp/recall-closure/uploads
LOG_LEVEL=INFO
```

For a live Gemini preview, change `AI_MODE` to `live` and add `GEMINI_API_KEY` as an encrypted Vercel environment variable. Do not prefix it with `NEXT_PUBLIC_` or expose it to browser code.

## 6. Verify before deploying

```bat
.venv\Scripts\python.exe scripts\vercel_preflight.py
```

To validate a complete environment locally, set the same variables in the current shell and run:

```bat
.venv\Scripts\python.exe scripts\vercel_preflight.py --check-env
```

After deployment:

```bat
curl.exe https://PROJECT-NAME.vercel.app/healthz
curl.exe https://PROJECT-NAME.vercel.app/api/readiness
curl.exe -I https://PROJECT-NAME.vercel.app/
```

Expected: HTTP `200`, JSON status `ok`, `deployment_target` equal to `vercel`, and the HTML marker `data-app-id="food-bank-recall-closure-agent"`.

## 7. Optional Vercel CLI deployment

The dashboard import is safer for a first deployment. CLI equivalent:

```bat
npm install -g vercel@latest
vercel login
vercel link
vercel --prod
```

The official FastAPI documentation requires Vercel CLI 48.1.8 or newer.

## Vercel limitations

- Hobby is free within limits and restricted to personal, non-commercial use. A hackathon preview must remain non-commercial.
- A Function request or response body is limited to 4.5 MB; this release caps uploads at 4,000,000 bytes.
- The Python bundle limit is 500 MB uncompressed.
- In-memory state and `/tmp` media are ephemeral. A cold start or another Function instance can lose them.
- Use Cloud Run + Firestore + Cloud Storage for the durable proof-of-action recording.
- Never upload a service-account JSON key. If Vercel must access Google Cloud, prefer Vercel OIDC with Google Workload Identity Federation and narrowly scoped IAM.

## Official references

- https://vercel.com/docs/frameworks/backend/fastapi
- https://vercel.com/docs/functions/runtimes/python
- https://vercel.com/docs/functions/limitations
- https://vercel.com/docs/plans/hobby
- https://vercel.com/docs/oidc/gcp
- https://cli.github.com/manual/gh_repo_create
- https://docs.github.com/en/migrations/importing-source-code/using-the-command-line-to-import-source-code/adding-locally-hosted-code-to-github
