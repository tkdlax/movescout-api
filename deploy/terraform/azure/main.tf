terraform {
  required_version = ">= 1.5"
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 4.0"
    }
  }
}

# Stub module — expand when migrating to Azure.
# See deploy/terraform/README.md for migration runbook.

variable "environment" {
  type        = string
  description = "Deployment environment (staging, production)"
  default     = "staging"
}

variable "location" {
  type    = string
  default = "eastus"
}

provider "azurerm" {
  features {}
}

# TODO: Resource group, Container Apps environment, Azure Database for PostgreSQL
# Flexible Server, Key Vault, Application Gateway or Front Door, ACR, Log Analytics.

output "migration_status" {
  value = "Terraform stubs only — see deploy/terraform/README.md"
}
