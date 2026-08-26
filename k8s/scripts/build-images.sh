#!/bin/sh

set -eu

ROOT_DIR="$(cd "$(dirname "$0")/../.." && pwd)"

IMAGE_TAG="${IMAGE_TAG:-dev}"
IMAGE_PREFIX="${IMAGE_PREFIX:-marketpulse}"
REGISTRY="${REGISTRY:-}"

image_ref() {
  image_name="$1"

  if [ -n "$REGISTRY" ]; then
    printf "%s/%s-%s:%s" "$REGISTRY" "$IMAGE_PREFIX" "$image_name" "$IMAGE_TAG"
  else
    printf "%s-%s:%s" "$IMAGE_PREFIX" "$image_name" "$IMAGE_TAG"
  fi
}

extract_configmap_value() {
  key_name="$1"

  sed -n "s/^[[:space:]]*$key_name:[[:space:]]*//p" "$ROOT_DIR/k8s/frontend/configmap.yaml" | tail -n 1
}

require_non_empty() {
  variable_name="$1"
  variable_value="$2"

  if [ -z "$variable_value" ]; then
    echo "Required frontend build value is missing: $variable_name" >&2
    exit 1
  fi
}

build_image() {
  service_name="$1"
  dockerfile_path="$2"

  image="$(image_ref "$service_name")"

  echo "Building $image from $dockerfile_path"
  docker build -f "$dockerfile_path" -t "$image" "$ROOT_DIR"
}

build_frontend_image() {
  image="$(image_ref "frontend")"
  next_public_api_base_url="$(extract_configmap_value "NEXT_PUBLIC_API_BASE_URL")"
  marketpulse_openapi_url="$(extract_configmap_value "MARKETPULSE_OPENAPI_URL")"
  next_public_supabase_url="$(extract_configmap_value "NEXT_PUBLIC_SUPABASE_URL")"
  next_public_supabase_publishable_key="$(extract_configmap_value "NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY")"

  require_non_empty "NEXT_PUBLIC_API_BASE_URL" "$next_public_api_base_url"
  require_non_empty "MARKETPULSE_OPENAPI_URL" "$marketpulse_openapi_url"
  require_non_empty "NEXT_PUBLIC_SUPABASE_URL" "$next_public_supabase_url"
  require_non_empty "NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY" "$next_public_supabase_publishable_key"

  echo "Building $image from $ROOT_DIR/k8s/frontend/Dockerfile.dev"
  docker build \
    -f "$ROOT_DIR/k8s/frontend/Dockerfile.dev" \
    -t "$image" \
    --build-arg "NEXT_PUBLIC_API_BASE_URL=$next_public_api_base_url" \
    --build-arg "MARKETPULSE_OPENAPI_URL=$marketpulse_openapi_url" \
    --build-arg "NEXT_PUBLIC_SUPABASE_URL=$next_public_supabase_url" \
    --build-arg "NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY=$next_public_supabase_publishable_key" \
    "$ROOT_DIR"
}

build_image "backend" "$ROOT_DIR/k8s/backend/Dockerfile.dev"
build_frontend_image
build_image "market-data-api" "$ROOT_DIR/k8s/market-data-api/Dockerfile.dev"
build_image "cron" "$ROOT_DIR/k8s/cron/Dockerfile.dev"

echo "All images built successfully."
