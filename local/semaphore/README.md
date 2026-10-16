# Local Semaphore project

This Compose project preserves the existing `valensys-t2-semaphore` service and its `valensys-t2-semaphore_semaphore-data` volume. It binds Semaphore to `127.0.0.1:3000`, adds pinned `helm` and `yq` task tools, and mounts the supplied repository read-only at `/workspace` for local checks. It does not need a cluster or cloud credentials.

## Existing installation and recovery

Keep the existing private credentials file outside this repository. In the shell, set `SEMAPHORE_ENV_FILE` to its path; do not print or copy its contents. Start or rebuild with `local/semaphore/start.sh`, and stop with `local/semaphore/stop.sh`. Stop does not remove volumes. Never use `docker compose down -v` for this installation.

After a checkout or host recovery, confirm the private credentials file and the named Docker volume still exist, then start the service. If the credentials file is missing, restore it from the owner's private backup. If the service image needs recovery, `start.sh` rebuilds the image and reuses the same named volume. Preserve the database and do not migrate it as part of routine recovery.

## Configure the API token

Start Semaphore and sign in at `http://127.0.0.1:3000`. Create an API token for the admin user in the Semaphore UI, then set `SEMAPHOREUI_API_TOKEN` in the current shell or a private shell environment manager. Do not put it in `.env`, `terraform.tfvars`, command arguments, or reports. The provider uses `http://127.0.0.1:3000/api` by default; override with `SEMAPHOREUI_API_BASE_URL` if needed.

The official `semaphoreui/semaphore` Terraform provider manages the project, no-credentials key, repository, local inventory, variable group, and templates. It is pinned to 0.3.9. Its published test matrix covers Semaphore 2.16.x through 2.18.x, not 2.19.12. Before the first apply on this installation, verify the running version from the Semaphore UI or container image metadata (`GET /api/ping` checks reachability only) and perform a read-only `terraform plan`; the parent operator must verify provider compatibility against this 2.19.12 service before applying. Do not proceed to apply if plan or provider refresh fails.

## Apply and repeat apply

From the repository root, after the service and token are ready:

```sh
local/semaphore/apply.sh -var='repository_url=https://github.com/alecuvalentin22/gcp-setup.git' -var='repository_branch=main'
local/semaphore/apply.sh -var='repository_url=https://github.com/alecuvalentin22/gcp-setup.git' -var='repository_branch=main'
```

Review the first plan before confirming apply. The second run should report no changes. Terraform state and provider cache remain local and are ignored by Git. Back up the state privately because it contains Semaphore resource metadata.

For an immediate local run from the mounted source, override the repository URL with `file:///workspace` and branch with the supplied checkout's current branch. The bind mount is read-only; do not use this local source URL as the public repository connection for normal operation.

## Run a task

In Semaphore, open project `gcp-setup`, select one of `YAML syntax`, `Helm lint`, or `Helm render`, then start a task and inspect its result. Each checks only repository files. The scripts are in `tasks/`; task tools are installed in the custom image at pinned Helm 3.16.4 and yq 4.44.3 releases with official checksums verified during build.

## Host-only verification

The worker environment may not have access to the Docker socket or the running host service. On the operator host, set `SEMAPHORE_ENV_FILE` and optionally `SEMAPHORE_REPOSITORY_PATH` (defaults to this checkout), run `local/semaphore/start.sh`, apply the project, run one validation task, and repeat the apply to verify no drift. Record task result and plan summary without recording the token or credentials. `local/semaphore/stop.sh` stops the service while retaining data.
