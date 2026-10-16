#!/bin/sh
set -eu
repo_root=$(git -C "$(dirname "$0")" rev-parse --show-toplevel)
: "${SEMAPHOREUI_API_TOKEN:?Set the API token in your shell environment}"
terraform -chdir="$repo_root/local/semaphore" init -input=false
terraform -chdir="$repo_root/local/semaphore" apply "$@"
