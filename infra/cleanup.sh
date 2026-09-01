#!/usr/bin/env bash
source "$(dirname "$0")/_common.sh"
if [[ "${CONFIRM_CLEANUP:-}" != "DELETE_RECALL_CLOSURE_RESOURCES" ]]; then
  printf 'Refusing cleanup. Set CONFIRM_CLEANUP=DELETE_RECALL_CLOSURE_RESOURCES.\n' >&2
  exit 2
fi
gcloud pubsub subscriptions delete "$PUBSUB_SUBSCRIPTION" --quiet || true
gcloud pubsub topics delete "$PUBSUB_TOPIC" "$PUBSUB_DLQ_TOPIC" --quiet || true
gcloud run services delete "$SERVICE_NAME" --region "$GOOGLE_CLOUD_REGION" --quiet || true
if [[ "${DELETE_EVIDENCE_BUCKET:-false}" == "true" ]]; then
  gcloud storage rm --recursive "gs://${GCS_BUCKET}/**" || true
  gcloud storage buckets delete "gs://${GCS_BUCKET}" --quiet || true
fi
printf 'Service and Pub/Sub resources removed. Firestore and secrets were intentionally retained.\n'
