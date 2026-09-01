#!/usr/bin/env bash
set -euo pipefail
URL="${1:?Usage: smoke_test.sh SERVICE_URL}"
if curl --fail --silent --show-error "${URL}/healthz" | python -m json.tool; then
  printf 'Public/read-only health smoke passed.\n'
else
  TOKEN="$(gcloud auth print-identity-token)"
  curl --fail --silent --show-error -H "Authorization: Bearer ${TOKEN}" "${URL}/healthz" | python -m json.tool
  printf 'Authenticated health smoke passed.\n'
fi
