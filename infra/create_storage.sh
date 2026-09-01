#!/usr/bin/env bash
source "$(dirname "$0")/_common.sh"
if ! gcloud storage buckets describe "gs://${GCS_BUCKET}" >/dev/null 2>&1; then
  gcloud storage buckets create "gs://${GCS_BUCKET}" --location="$GOOGLE_CLOUD_REGION" --uniform-bucket-level-access
fi
gcloud storage buckets update "gs://${GCS_BUCKET}" --public-access-prevention
gcloud storage buckets add-iam-policy-binding "gs://${GCS_BUCKET}" --member="serviceAccount:${RUNTIME_SA}" --role=roles/storage.objectUser --condition=None >/dev/null
printf 'Private evidence bucket ready: gs://%s\n' "$GCS_BUCKET"
