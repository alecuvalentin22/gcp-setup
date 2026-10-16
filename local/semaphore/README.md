# Local Semaphore

This Compose project describes the existing local Semaphore 2.19.12 service. It binds only to `127.0.0.1:3000`, uses project `valensys-t2-semaphore`, and explicitly mounts the existing Docker volume `valensys-t2-semaphore_semaphore-data`. Keeping that volume name preserves the current SQLite database and Semaphore workspace.

## Existing installation: start and stop

The existing installation uses a private credentials file outside this repository. Set `SEMAPHORE_ENV_FILE` to its absolute path in your local shell. The file's location and contents belong in the owner's private operational records, rather than in this repository.

Use that existing file directly; do not print it, copy its values here, or replace it with `.env.example`. From the repository root, first check that the file is available:

```sh
: "${SEMAPHORE_ENV_FILE:?Set this to the existing private credentials file}"
test -r "$SEMAPHORE_ENV_FILE"
```

Then, when starting the service is authorized:

```sh
docker compose --project-name valensys-t2-semaphore \
  --env-file "$SEMAPHORE_ENV_FILE" \
  -f local/semaphore/compose.yaml up -d
```

Stop the service while retaining its data:

```sh
docker compose --project-name valensys-t2-semaphore \
  --env-file "$SEMAPHORE_ENV_FILE" \
  -f local/semaphore/compose.yaml down
```

Do not add `-v` to the stop command: that removes persistent data. After a repository recovery or fresh checkout, confirm the private credentials file remains available in the runtime directory before starting. If it is missing, restore it through the owner's private backup process; the example file contains placeholders and cannot recover the admin password or encryption key. The Docker volume is independent of this repository and must be preserved.

## New local installation

For a genuinely new installation only, copy `.env.example` to `.env`, replace both placeholders with private values, then use Compose from this directory. Generate a key with `openssl rand -base64 32`. The root `.gitignore` excludes `.env` and Terraform state.

## Read-only repository checks

From the repository root, these checks validate YAML syntax, lint the podinfo chart for dev and prod, and render both configurations:

```sh
find . -type f \( -name "*.yaml" -o -name "*.yml" \) ! -path "*/templates/*" ! -path "./.git/*" | while read f; do /opt/homebrew/bin/yq e "." "$f" >/dev/null || { echo "invalid YAML: $f"; exit 1; }; done
for v in dev prod; do /opt/homebrew/bin/helm lint charts/podinfo-app -f "charts/podinfo-app/values-$v.yaml" || exit 1; done
for v in dev prod; do /opt/homebrew/bin/helm template podinfo charts/podinfo-app -f "charts/podinfo-app/values-$v.yaml" >/dev/null || exit 1; done
```

These tasks are local and read-only; they do not access a cluster or cloud credentials.
