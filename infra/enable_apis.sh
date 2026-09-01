#!/usr/bin/env bash
source "$(dirname "$0")/_common.sh"
gcloud services enable \
  run.googleapis.com artifactregistry.googleapis.com cloudbuild.googleapis.com \
  firestore.googleapis.com storage.googleapis.com pubsub.googleapis.com \
  secretmanager.googleapis.com aiplatform.googleapis.com iamcredentials.googleapis.com
printf 'Required APIs enabled.\n'
