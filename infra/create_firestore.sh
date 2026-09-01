#!/usr/bin/env bash
source "$(dirname "$0")/_common.sh"
FIRESTORE_LOCATION="${FIRESTORE_LOCATION:-$GOOGLE_CLOUD_REGION}"
if gcloud firestore databases describe --database='(default)' >/dev/null 2>&1; then
  printf 'Firestore (default) already exists.\n'
else
  gcloud firestore databases create --database='(default)' --location="$FIRESTORE_LOCATION" --type=firestore-native
fi
