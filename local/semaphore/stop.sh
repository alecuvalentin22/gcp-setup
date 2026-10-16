#!/bin/sh
set -eu
repo_root=$(git -C "$(dirname "$0")" rev-parse --show-toplevel)
: "${SEMAPHORE_ENV_FILE:?Set SEMAPHORE_ENV_FILE to the existing private credentials file}"
test -r "$SEMAPHORE_ENV_FILE"
export SEMAPHORE_REPOSITORY_PATH=${SEMAPHORE_REPOSITORY_PATH:-$repo_root}
exec docker compose --project-name valensys-t2-semaphore --env-file "$SEMAPHORE_ENV_FILE" \
  -f "$repo_root/local/semaphore/compose.yaml" down
