#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT="${1:-/data/food-bank-recall-closure-agent.zip}"
STAGE="$(mktemp -d /tmp/recall-closure-release.XXXXXX)"
CANONICAL_ROOT="$STAGE/food-bank-recall-closure-agent"
cleanup(){ rm -rf "$STAGE"; }
trap cleanup EXIT

if [[ "${SKIP_FINALIZE:-false}" != "true" ]]; then
  python3 "$ROOT/scripts/finalize_release.py"
fi

mkdir -p "$CANONICAL_ROOT"
tar -C "$ROOT" \
  --exclude='.git' --exclude='.venv' --exclude='__pycache__' --exclude='.pytest_cache' \
  --exclude='.ruff_cache' --exclude='runtime' --exclude='release-validation' --exclude='preview' \
  --exclude='htmlcov' --exclude='.env' --exclude='.env.cloud.generated' --exclude='gcp-readiness.json' \
  --exclude='.coverage' --exclude='.DS_Store' --exclude='credentials.json' \
  --exclude='service-account*.json' --exclude='*.pyc' --exclude='*.pyo' --exclude='*.zip' \
  -cf - . | tar -C "$CANONICAL_ROOT" -xf -

rm -f "$OUT"
(
  cd "$STAGE"
  zip -q -r "$OUT" food-bank-recall-closure-agent
)
python3 "$ROOT/scripts/validate_release.py" "$OUT"
