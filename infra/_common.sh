#!/usr/bin/env bash
set -euo pipefail
: "${GOOGLE_CLOUD_PROJECT:?Set GOOGLE_CLOUD_PROJECT}"
GOOGLE_CLOUD_REGION="${GOOGLE_CLOUD_REGION:-us-central1}"
SERVICE_NAME="${SERVICE_NAME:-recall-closure-agent}"
ARTIFACT_REPOSITORY="${ARTIFACT_REPOSITORY:-recall-closure}"
RUNTIME_SA_NAME="${RUNTIME_SA_NAME:-recall-closure-runtime}"
RUNTIME_SA="${RUNTIME_SA_NAME}@${GOOGLE_CLOUD_PROJECT}.iam.gserviceaccount.com"
PUSH_SA_NAME="${PUSH_SA_NAME:-recall-closure-push}"
PUSH_SA="${PUSH_SA_NAME}@${GOOGLE_CLOUD_PROJECT}.iam.gserviceaccount.com"
GCS_BUCKET="${GCS_BUCKET:-recall-closure-evidence-${GOOGLE_CLOUD_PROJECT}}"
PUBSUB_TOPIC="${PUBSUB_TOPIC:-recall-notices}"
PUBSUB_DLQ_TOPIC="${PUBSUB_DLQ_TOPIC:-recall-notices-dead-letter}"
PUBSUB_SUBSCRIPTION="${PUBSUB_SUBSCRIPTION:-recall-closure-push}"
CLOUD_RUN_MAX_INSTANCES="${CLOUD_RUN_MAX_INSTANCES:-1}"
CLOUD_RUN_MIN_INSTANCES="${CLOUD_RUN_MIN_INSTANCES:-0}"
gcloud config set project "$GOOGLE_CLOUD_PROJECT" >/dev/null
