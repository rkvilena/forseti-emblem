#!/usr/bin/env bash
# Usage:
#   ./infrastructure/cloudbuild/build.sh <path-to-Dockerfile-relative-to-repo-root> [port] [env-file]
# Examples:
#   ./infrastructure/cloudbuild/build.sh infrastructure/cloudbuild/backend/Dockerfile 8080 backend/.env
#   ./infrastructure/cloudbuild/build.sh infrastructure/cloudbuild/frontend/Dockerfile 3000 frontend/.env
set -euo pipefail

if [ $# -lt 1 ]; then
  echo "Usage: $0 <path-to-Dockerfile-relative-to-repo-root> [port] [env-file]" >&2
  exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"

DOCKERFILE_REL="$1"
DOCKERFILE_PATH="$ROOT_DIR/$DOCKERFILE_REL"
PORT="${2:-8080}"
ENV_FILE_REL="${3:-}"

if [ ! -f "$DOCKERFILE_PATH" ]; then
  echo "Dockerfile not found: $DOCKERFILE_PATH" >&2
  exit 1
fi

EXPOSE_PORT="$(grep -iE '^EXPOSE[[:space:]]+[0-9]+' "$DOCKERFILE_PATH" | awk '{print $2}' | head -n1 || true)"
if [ -n "${EXPOSE_PORT:-}" ]; then
  PORT="$EXPOSE_PORT"
fi

IMAGE_TAG="test-$(basename "$(dirname "$DOCKERFILE_PATH")")-$(date +%s)"
CONTAINER_NAME="${IMAGE_TAG}-container"

CONTEXT_DIR="$ROOT_DIR"

BUILD_ARGS=()

cleanup() {
  docker rm -f "$CONTAINER_NAME" >/dev/null 2>&1 || true
}
trap cleanup EXIT INT TERM

ENV_ARGS=()
if [ -n "$ENV_FILE_REL" ]; then
  ENV_FILE_PATH="$ROOT_DIR/$ENV_FILE_REL"
  if [ ! -f "$ENV_FILE_PATH" ]; then
    echo "Env file not found: $ENV_FILE_PATH" >&2
    exit 1
  fi
  ENV_ARGS+=(--env-file "$ENV_FILE_PATH")

  NEXT_PUBLIC_API_URL_VALUE="$(grep -E '^NEXT_PUBLIC_API_URL=' "$ENV_FILE_PATH" | tail -n1 | cut -d '=' -f2- || true)"
  if [ -n "$NEXT_PUBLIC_API_URL_VALUE" ]; then
    if [[ "$NEXT_PUBLIC_API_URL_VALUE" =~ ^\".*\"$ || "$NEXT_PUBLIC_API_URL_VALUE" =~ ^\'.*\'$ ]]; then
      NEXT_PUBLIC_API_URL_VALUE="${NEXT_PUBLIC_API_URL_VALUE:1:${#NEXT_PUBLIC_API_URL_VALUE}-2}"
    fi
    BUILD_ARGS+=(--build-arg "NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL_VALUE")
  fi

  NEXT_PUBLIC_TURNSTILE_SITE_KEY_VALUE="$(grep -E '^NEXT_PUBLIC_TURNSTILE_SITE_KEY=' "$ENV_FILE_PATH" | tail -n1 | cut -d '=' -f2- || true)"
  if [ -n "$NEXT_PUBLIC_TURNSTILE_SITE_KEY_VALUE" ]; then
    if [[ "$NEXT_PUBLIC_TURNSTILE_SITE_KEY_VALUE" =~ ^\".*\"$ || "$NEXT_PUBLIC_TURNSTILE_SITE_KEY_VALUE" =~ ^\'.*\'$ ]]; then
      NEXT_PUBLIC_TURNSTILE_SITE_KEY_VALUE="${NEXT_PUBLIC_TURNSTILE_SITE_KEY_VALUE:1:${#NEXT_PUBLIC_TURNSTILE_SITE_KEY_VALUE}-2}"
    fi
    BUILD_ARGS+=(--build-arg "NEXT_PUBLIC_TURNSTILE_SITE_KEY=$NEXT_PUBLIC_TURNSTILE_SITE_KEY_VALUE")
  fi

  NEXT_PUBLIC_CHAT_STORAGE_KEY_VALUE="$(grep -E '^NEXT_PUBLIC_CHAT_STORAGE_KEY=' "$ENV_FILE_PATH" | tail -n1 | cut -d '=' -f2- || true)"
  if [ -n "$NEXT_PUBLIC_CHAT_STORAGE_KEY_VALUE" ]; then
    if [[ "$NEXT_PUBLIC_CHAT_STORAGE_KEY_VALUE" =~ ^\".*\"$ || "$NEXT_PUBLIC_CHAT_STORAGE_KEY_VALUE" =~ ^\'.*\'$ ]]; then
      NEXT_PUBLIC_CHAT_STORAGE_KEY_VALUE="${NEXT_PUBLIC_CHAT_STORAGE_KEY_VALUE:1:${#NEXT_PUBLIC_CHAT_STORAGE_KEY_VALUE}-2}"
    fi
    BUILD_ARGS+=(--build-arg "NEXT_PUBLIC_CHAT_STORAGE_KEY=$NEXT_PUBLIC_CHAT_STORAGE_KEY_VALUE")
  fi

  NODE_ENV_VALUE="$(grep -E '^NODE_ENV=' "$ENV_FILE_PATH" | tail -n1 | cut -d '=' -f2- || true)"
  if [ -n "$NODE_ENV_VALUE" ]; then
    if [[ "$NODE_ENV_VALUE" =~ ^\".*\"$ || "$NODE_ENV_VALUE" =~ ^\'.*\'$ ]]; then
      NODE_ENV_VALUE="${NODE_ENV_VALUE:1:${#NODE_ENV_VALUE}-2}"
    fi
    BUILD_ARGS+=(--build-arg "NODE_ENV=$NODE_ENV_VALUE")
  fi
fi

echo "Building image '${IMAGE_TAG}' from '${DOCKERFILE_REL}' (context: ${CONTEXT_DIR}) with build args: ${BUILD_ARGS[*]}..."
docker build -f "$DOCKERFILE_PATH" -t "$IMAGE_TAG" "${BUILD_ARGS[@]}" "$CONTEXT_DIR"

echo "Running container '${CONTAINER_NAME}' on port ${PORT}..."
docker run -d --name "$CONTAINER_NAME" -e PORT="$PORT" "${ENV_ARGS[@]}" -p "${PORT}:${PORT}" "$IMAGE_TAG"

echo "Waiting for the app to become ready..."
for i in {1..30}; do
  echo "Health check attempt ${i}/30..."
  if curl -fsS "http://localhost:${PORT}/health" >/dev/null 2>&1 || \
     curl -fsS "http://localhost:${PORT}/" >/dev/null 2>&1; then
    echo "App is responding on port ${PORT}. Dockerfile deployment looks OK."
    echo "Attaching to container logs. Press Ctrl+C when you're done; the container will then be stopped and removed."
    docker logs -f "$CONTAINER_NAME"
    exit 0
  fi

  # Every 5 attempts, show the latest container logs to help debug why it's not ready
  if [ $((i % 5)) -eq 0 ]; then
    echo "Container logs after attempt ${i}:"
    docker logs --tail 40 "$CONTAINER_NAME" || true
  fi

  sleep 1
done

echo "App did not respond on port ${PORT} within the timeout window." >&2
echo "Final container logs:"
docker logs --tail 80 "$CONTAINER_NAME" || true
exit 1
