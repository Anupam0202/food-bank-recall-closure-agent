#!/usr/bin/env bash
source "$(dirname "$0")/_common.sh"
ALLOW_PUBLIC_READS="${ALLOW_PUBLIC_READS:-true}"
PENDING_URL="https:""//pending.invalid"
"$(dirname "$0")/enable_apis.sh"
if ! gcloud artifacts repositories describe "$ARTIFACT_REPOSITORY" --location "$GOOGLE_CLOUD_REGION" >/dev/null 2>&1; then
  gcloud artifacts repositories create "$ARTIFACT_REPOSITORY" --repository-format=docker --location="$GOOGLE_CLOUD_REGION"
fi
"$(dirname "$0")/create_service_account.sh"
"$(dirname "$0")/create_firestore.sh"
"$(dirname "$0")/create_storage.sh"
TAG="${IMAGE_TAG:-$(git rev-parse --short HEAD 2>/dev/null || date +%Y%m%d%H%M%S)}"
IMAGE="${GOOGLE_CLOUD_REGION}-docker.pkg.dev/${GOOGLE_CLOUD_PROJECT}/${ARTIFACT_REPOSITORY}/${SERVICE_NAME}:${TAG}"
gcloud builds submit --tag "$IMAGE" .
gcloud run deploy "$SERVICE_NAME" --image "$IMAGE" --region "$GOOGLE_CLOUD_REGION" --platform=managed \
  --no-allow-unauthenticated --service-account="$RUNTIME_SA" --port=8080 --timeout=300 \
  --concurrency=20 --min-instances="$CLOUD_RUN_MIN_INSTANCES" --max-instances="$CLOUD_RUN_MAX_INSTANCES" --cpu=1 --memory=512Mi --cpu-throttling \
  --set-env-vars="APP_ENV=production,APP_BASE_URL=${PENDING_URL},AI_MODE=live,MODEL_NAME=gemini-3.7-flash,MODEL_MAX_ATTEMPTS=3,USE_FIRESTORE=true,USE_CLOUD_STORAGE=true,GOOGLE_CLOUD_PROJECT=${GOOGLE_CLOUD_PROJECT},GOOGLE_CLOUD_REGION=${GOOGLE_CLOUD_REGION},GCS_BUCKET=${GCS_BUCKET},FIRESTORE_DATABASE=(default),PUBSUB_VERIFICATION_AUDIENCE=${PENDING_URL},CLOUD_COST_PROFILE=free-tier,CLOUD_RUN_MAX_INSTANCES=${CLOUD_RUN_MAX_INSTANCES}" \
  --set-secrets="GEMINI_API_KEY=gemini-api-key:latest,SESSION_SECRET=session-secret:latest,DEMO_ADMIN_TOKEN=demo-admin-token:latest"
SERVICE_URL="$(gcloud run services describe "$SERVICE_NAME" --region "$GOOGLE_CLOUD_REGION" --format='value(status.url)')"
gcloud run services update "$SERVICE_NAME" --region "$GOOGLE_CLOUD_REGION" --update-env-vars="APP_BASE_URL=${SERVICE_URL},PUBSUB_VERIFICATION_AUDIENCE=${SERVICE_URL}" >/dev/null
if [[ "$ALLOW_PUBLIC_READS" == "true" ]]; then
  gcloud run services add-iam-policy-binding "$SERVICE_NAME" --region "$GOOGLE_CLOUD_REGION" --member=allUsers --role=roles/run.invoker --condition=None >/dev/null
fi
SERVICE_URL="$SERVICE_URL" "$(dirname "$0")/create_pubsub.sh"
printf 'Cloud Run URL: %s\n' "$SERVICE_URL"
"$(dirname "$0")/smoke_test.sh" "$SERVICE_URL"
