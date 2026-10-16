# Local Semaphore as code

This setup manages the gcp-setup project, a public GitHub connection, a local read-only repository, inventory, variable group, and three templates: YAML syntax, Helm lint, and Helm render. Tasks use /workspace directly, so unpushed changes work without cloud credentials.

The service listens at http://127.0.0.1:3000. Compose retains project `valensys-t2-semaphore` and volume `valensys-t2-semaphore_semaphore-data`. The image retains Semaphore 2.19.12 and adds checksum-verified Helm 3.16.4 and yq 4.44.3. The official Terraform provider is pinned to 0.3.9 with a committed lock file.

## Setup and verify

Requirements: Docker Compose, Terraform 1.5 or newer, Python 3, the existing running service, and its private credentials file. Retain the existing SEMAPHORE_ADMIN_PASSWORD and SEMAPHORE_ACCESS_KEY_ENCRYPTION values.

```sh
export SEMAPHORE_ENV_FILE=/path/to/private/credentials.env
export SEMAPHORE_STATE_DIR="$HOME/.local/state/gcp-setup-semaphore"
python3 local/semaphore/manage.py setup --yes
```

Setup checks the actual Docker project and volume, makes and verifies a consistent SQLite backup, rebuilds the image, and reuses the existing volume. It signs in, creates or reuses a dedicated API token, applies Terraform, requires a second plan with no changes, then runs all three tasks and checks their terminal results. It prints task IDs and statuses. No manual UI configuration is needed. Omit --yes for interactive apply.

The mounted repository defaults to this checkout; override SEMAPHORE_REPOSITORY_PATH if needed. Keep it available while using local tasks. The separate public repository connection defaults to https://github.com/alecuvalentin22/gcp-setup.git, branch main. Terraform -var arguments can override these without changing local task source.

## Repeat apply and verification

```sh
local/semaphore/apply.sh --yes
python3 local/semaphore/manage.py verify
```

Apply refreshes resources and requires a subsequent no-change plan. Verify launches the templates again and saves their outputs privately. The same templates are available in the UI. These tasks do not deploy cloud resources.

State, token, database backups and reports stay outside Git in SEMAPHORE_STATE_DIR (default shown above). Preserve this directory and the private credentials file. Reuse the same state directory to avoid duplicate projects. If state is lost, restore it or import the existing resources before applying again. Treat the entire directory as private.

## Service and recovery

start.sh rebuilds/starts the service; stop.sh stops it while retaining data. Never use docker compose down -v. `python3 local/semaphore/manage.py backup` creates another verified online database backup. Back up state and credentials privately before host changes.

Routine restart/rebuild reuses the existing volume and keys. Restore missing credentials or state from private backups. Database restore requires stopping the service, preserving the original volume, and restoring a verified SQLite backup with correct ownership. Never replace a live database. No automatic database restore or migration is performed.
