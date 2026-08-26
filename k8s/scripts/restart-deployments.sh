#!/bin/sh

set -eu

ROOT_DIR="$(cd "$(dirname "$0")/../.." && pwd)"
NAMESPACE="${NAMESPACE:-marketpulse}"
SECRETS_DIR="${SECRETS_DIR:-$ROOT_DIR/k8s/secrets}"
CRON_MANIFESTS_DIR="${CRON_MANIFESTS_DIR:-$ROOT_DIR/k8s/cron}"

require_file() {
  file_path="$1"

  if [ ! -f "$file_path" ]; then
    echo "Required secret env file not found: $file_path" >&2
    exit 1
  fi
}

make_temp_env_with_generated_secret_key_base() {
  source_env_file="$1"
  temp_env_file="$2"

  cp "$source_env_file" "$temp_env_file"

  if ! grep -q '^SECRET_KEY_BASE=' "$temp_env_file"; then
    if command -v openssl >/dev/null 2>&1; then
      generated_secret_key_base="$(openssl rand -hex 64)"
    else
      echo "openssl is required to generate SECRET_KEY_BASE automatically" >&2
      exit 1
    fi

    printf '\nSECRET_KEY_BASE=%s\n' "$generated_secret_key_base" >> "$temp_env_file"
  fi
}

apply_secret() {
  secret_name="$1"
  env_file="$2"

  require_file "$env_file"

  echo "Applying secret/$secret_name from $env_file"
  kubectl create secret generic "$secret_name" \
    -n "$NAMESPACE" \
    --from-env-file="$env_file" \
    --dry-run=client \
    -o yaml | kubectl apply -f -
}

apply_market_data_api_secret() {
  env_file="$1"
  temp_env_file="$(mktemp)"

  require_file "$env_file"
  trap 'rm -f "$temp_env_file"' EXIT

  make_temp_env_with_generated_secret_key_base "$env_file" "$temp_env_file"
  apply_secret "marketpulse-market-data-api-secrets" "$temp_env_file"

  rm -f "$temp_env_file"
  trap - EXIT
}

restart_deployment() {
  deployment_name="$1"
  echo "Restarting deployment/$deployment_name in namespace $NAMESPACE"
  kubectl rollout restart "deployment/$deployment_name" -n "$NAMESPACE"
}

echo "Applying namespace manifest"
kubectl apply -f "$ROOT_DIR/k8s/namespace.yaml"

apply_secret "marketpulse-postgres-secrets" "$SECRETS_DIR/postgres.env"
apply_secret "marketpulse-backend-secrets" "$SECRETS_DIR/backend.env"
apply_market_data_api_secret "$SECRETS_DIR/market-data-api.env"

echo "Applying non-cron manifests"
kubectl apply \
  -f "$ROOT_DIR/k8s/backend/configmap.yaml" \
  -f "$ROOT_DIR/k8s/backend/deployment.yaml" \
  -f "$ROOT_DIR/k8s/backend/service.yaml" \
  -f "$ROOT_DIR/k8s/backend/ingress.yaml" \
  -f "$ROOT_DIR/k8s/frontend/configmap.yaml" \
  -f "$ROOT_DIR/k8s/frontend/deployment.yaml" \
  -f "$ROOT_DIR/k8s/frontend/service.yaml" \
  -f "$ROOT_DIR/k8s/frontend/ingress.yaml" \
  -f "$ROOT_DIR/k8s/market-data-api/configmap.yaml" \
  -f "$ROOT_DIR/k8s/market-data-api/deployment.yaml" \
  -f "$ROOT_DIR/k8s/market-data-api/service.yaml" \
  -f "$ROOT_DIR/k8s/postgres/persistentvolumeclaim.yaml" \
  -f "$ROOT_DIR/k8s/postgres/deployment.yaml" \
  -f "$ROOT_DIR/k8s/postgres/service.yaml" \
  -f "$ROOT_DIR/k8s/redis/persistentvolumeclaim.yaml" \
  -f "$ROOT_DIR/k8s/redis/deployment.yaml" \
  -f "$ROOT_DIR/k8s/redis/service.yaml"

echo "Running database migrations"
sh "$ROOT_DIR/k8s/scripts/run-migrations.sh"

echo "Applying cron kustomize manifests"
kubectl apply -k "$CRON_MANIFESTS_DIR"

restart_deployment "marketpulse-backend"
restart_deployment "marketpulse-frontend"
restart_deployment "marketpulse-market-data-api"

echo "Applied secrets, applied non-cron manifests, ran database migrations, applied cron manifests, and requested rollout restart for application deployments."
