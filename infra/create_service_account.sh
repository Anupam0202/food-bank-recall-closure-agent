#!/usr/bin/env bash
source "$(dirname "$0")/_common.sh"
if ! gcloud iam service-accounts describe "$RUNTIME_SA" >/dev/null 2>&1; then
  gcloud iam service-accounts create "$RUNTIME_SA_NAME" --display-name="Recall Closure runtime"
fi
for role in roles/datastore.user roles/logging.logWriter; do
  gcloud projects add-iam-policy-binding "$GOOGLE_CLOUD_PROJECT" --member="serviceAccount:${RUNTIME_SA}" --role="$role" --condition=None >/dev/null
 done
for secret in gemini-api-key session-secret demo-admin-token; do
  if ! gcloud secrets describe "$secret" >/dev/null 2>&1; then
    printf 'Missing Secret Manager secret: %s\nCreate it before deployment.\n' "$secret" >&2
    exit 1
  fi
  gcloud secrets add-iam-policy-binding "$secret" --member="serviceAccount:${RUNTIME_SA}" --role=roles/secretmanager.secretAccessor --condition=None >/dev/null
 done
printf 'Runtime service account ready: %s\n' "$RUNTIME_SA"
