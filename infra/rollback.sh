#!/usr/bin/env bash
set -euo pipefail
: "${GOOGLE_CLOUD_PROJECT:?Set GOOGLE_CLOUD_PROJECT}"
REGION="${GOOGLE_CLOUD_REGION:-us-central1}"
SERVICE="${SERVICE_NAME:-recall-closure-agent}"
REVISION="${1:?Usage: rollback.sh REVISION_NAME}"
gcloud run services update-traffic "$SERVICE" --region "$REGION" --to-revisions "${REVISION}=100"
