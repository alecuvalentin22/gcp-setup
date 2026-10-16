terraform {
  backend "local" {}
  required_version = ">= 1.5.0"
  required_providers {
    semaphoreui = {
      source  = "semaphoreui/semaphore"
      version = "= 0.3.9"
    }
  }
}

provider "semaphoreui" {
  api_base_url = var.api_base_url
  # Read from SEMAPHOREUI_API_TOKEN in the environment. Never put it in tfvars.
}

variable "api_base_url" {
  type        = string
  description = "Semaphore API URL (include /api)."
  default     = "http://127.0.0.1:3000/api"
}

variable "repository_url" {
  type        = string
  description = "Public HTTPS repository connection."
  default     = "https://github.com/alecuvalentin22/gcp-setup.git"
}

variable "repository_branch" {
  type        = string
  description = "Branch to check out for the public repository connection."
  default     = "main"
}
