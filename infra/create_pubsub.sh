#!/usr/bin/env bash
source "$(dirname "$0")/_common.sh"
SERVICE_URL="${SERVICE_URL:-$(gcloud run services describe "$SERVICE_NAME" --region "$GOOGLE_CLOUD_REGION" --format='value(status.url)')}"
: "${SERVICE_URL:?Cloud Run service URL is required}"
if ! gcloud iam service-accounts describe "$PUSH_SA" >/dev/null 2>&1; then
  gcloud iam service-accounts create "$PUSH_SA_NAME" --display-name="Recall Closure Pub/Sub push"
fi
gcloud run services add-iam-policy-binding "$SERVICE_NAME" --region "$GOOGLE_CLOUD_REGION" --member="serviceAccount:${PUSH_SA}" --role=roles/run.invoker --condition=None >/dev/null
for topic in "$PUBSUB_TOPIC" "$PUBSUB_DLQ_TOPIC"; do
  gcloud pubsub topics describe "$topic" >/dev/null 2>&1 || gcloud pubsub topics create "$topic"
 done
if gcloud pubsub subscriptions describe "$PUBSUB_SUBSCRIPTION" >/dev/null 2>&1; then
  gcloud pubsub subscriptions update "$PUBSUB_SUBSCRIPTION" \
    --push-endpoint="${SERVICE_URL}/pubsub/recall" --push-auth-service-account="$PUSH_SA" \
    --push-auth-token-audience="$SERVICE_URL" --min-retry-delay=10s --max-retry-delay=300s \
    --dead-letter-topic="$PUBSUB_DLQ_TOPIC" --max-delivery-attempts=5 --ack-deadline=300
else
  gcloud pubsub subscriptions create "$PUBSUB_SUBSCRIPTION" --topic="$PUBSUB_TOPIC" \
    --push-endpoint="${SERVICE_URL}/pubsub/recall" --push-auth-service-account="$PUSH_SA" \
    --push-auth-token-audience="$SERVICE_URL" --min-retry-delay=10s --max-retry-delay=300s \
    --dead-letter-topic="$PUBSUB_DLQ_TOPIC" --max-delivery-attempts=5 --ack-deadline=300
fi
PROJECT_NUMBER="$(gcloud projects describe "$GOOGLE_CLOUD_PROJECT" --format='value(projectNumber)')"
PUBSUB_AGENT="service-${PROJECT_NUMBER}@gcp-sa-pubsub.iam.gserviceaccount.com"
gcloud pubsub topics add-iam-policy-binding "$PUBSUB_DLQ_TOPIC" --member="serviceAccount:${PUBSUB_AGENT}" --role=roles/pubsub.publisher --condition=None >/dev/null
gcloud pubsub subscriptions add-iam-policy-binding "$PUBSUB_SUBSCRIPTION" --member="serviceAccount:${PUBSUB_AGENT}" --role=roles/pubsub.subscriber --condition=None >/dev/null
printf 'Authenticated push subscription ready: %s\n' "$PUBSUB_SUBSCRIPTION"
