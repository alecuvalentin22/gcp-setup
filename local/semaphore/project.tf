resource "semaphoreui_project" "gcp_setup" {
  name               = "gcp-setup"
  alert              = false
  max_parallel_tasks = 1
}

resource "semaphoreui_project_key" "no_key" {
  project_id = semaphoreui_project.gcp_setup.id
  name       = "No credentials"
  none       = {}
}

resource "semaphoreui_project_repository" "source" {
  project_id = semaphoreui_project.gcp_setup.id
  name       = "gcp-setup source"
  url        = var.repository_url
  branch     = var.repository_branch
  ssh_key_id = semaphoreui_project_key.no_key.id
}

resource "semaphoreui_project_inventory" "local" {
  project_id = semaphoreui_project.gcp_setup.id
  name       = "Local only"
  ssh_key_id = semaphoreui_project_key.no_key.id
  static = {
    inventory = "localhost ansible_connection=local"
  }
}

resource "semaphoreui_project_environment" "checks" {
  project_id  = semaphoreui_project.gcp_setup.id
  name        = "Read-only repository checks"
  environment = {}
  variables   = {}
}

locals {
  checks = {
    "YAML syntax" = "local/semaphore/tasks/yaml-syntax.sh"
    "Helm lint"   = "local/semaphore/tasks/helm-lint.sh"
    "Helm render" = "local/semaphore/tasks/helm-render.sh"
  }
}

resource "semaphoreui_project_template" "checks" {
  for_each       = local.checks
  project_id     = semaphoreui_project.gcp_setup.id
  environment_id = semaphoreui_project_environment.checks.id
  inventory_id   = semaphoreui_project_inventory.local.id
  repository_id  = semaphoreui_project_repository.local.id
  name           = each.key
  app            = "bash"
  playbook       = each.value
  description    = "Local read-only validation from the supplied repository."
}

# Plain local paths use Semaphore's local repository mode; no Git push required.
resource "semaphoreui_project_repository" "local" {
  project_id = semaphoreui_project.gcp_setup.id
  name       = "Local read-only checkout"
  url        = "/workspace"
  branch     = var.repository_branch
  ssh_key_id = semaphoreui_project_key.no_key.id
}

output "project_id" { value = semaphoreui_project.gcp_setup.id }
output "template_ids" {
  value = { for name, template in semaphoreui_project_template.checks : name => template.id }
}
