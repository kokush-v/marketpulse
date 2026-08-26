#!/bin/sh

set -eu

ROOT_DIR="$(cd "$(dirname "$0")/../.." && pwd)"
NAMESPACE="${NAMESPACE:-marketpulse}"
JOB_NAME="marketpulse-backend-migrate"
POSTGRES_DEPLOYMENT="${POSTGRES_DEPLOYMENT:-marketpulse-postgres}"
WAIT_TIMEOUT="${WAIT_TIMEOUT:-180s}"
MAX_ATTEMPTS="${MAX_ATTEMPTS:-3}"

echo "Waiting for deployment/$POSTGRES_DEPLOYMENT to become available"
kubectl wait --for=condition=available "deployment/$POSTGRES_DEPLOYMENT" -n "$NAMESPACE" --timeout="$WAIT_TIMEOUT"

attempt=1
while [ "$attempt" -le "$MAX_ATTEMPTS" ]; do
  echo "Deleting previous migration job if it exists (attempt $attempt/$MAX_ATTEMPTS)"
  kubectl delete job "$JOB_NAME" -n "$NAMESPACE" --ignore-not-found=true
  kubectl wait --for=delete "job/$JOB_NAME" -n "$NAMESPACE" --timeout=60s >/dev/null 2>&1 || true

  echo "Creating migration job (attempt $attempt/$MAX_ATTEMPTS)"
  kubectl create -f "$ROOT_DIR/k8s/backend/migration-job.yaml"

  echo "Waiting for migration job completion (attempt $attempt/$MAX_ATTEMPTS)"
  if kubectl wait --for=condition=complete "job/$JOB_NAME" -n "$NAMESPACE" --timeout="$WAIT_TIMEOUT"; then
    echo "Migration job completed successfully."
    exit 0
  fi

  if [ "$attempt" -lt "$MAX_ATTEMPTS" ]; then
    echo "Migration job did not complete on attempt $attempt. Retrying..."
  fi

  attempt=$((attempt + 1))
done

echo "Migration job failed after $MAX_ATTEMPTS attempts." >&2
exit 1
