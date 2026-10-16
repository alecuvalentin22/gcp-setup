#!/bin/sh
set -eu
find . -type f \( -name '*.yaml' -o -name '*.yml' \) ! -path '*/templates/*' ! -path './.git/*' |
  while IFS= read -r file; do
    yq e '.' "$file" >/dev/null || { echo "invalid YAML: $file" >&2; exit 1; }
  done
