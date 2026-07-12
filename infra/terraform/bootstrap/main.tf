terraform {
  required_version = ">= 1.6"
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 4.0"
    }
  }
  # Local state on purpose: this bootstraps the remote backend itself.
}

provider "azurerm" {
  features {}
  subscription_id = var.subscription_id
}

variable "subscription_id" {
  type        = string
  description = "Azure subscription ID."
}

variable "location" {
  type    = string
  default = "westus2"
}

resource "azurerm_resource_group" "tfstate" {
  name     = "dmplt-tfstate-rg"
  location = var.location
  tags     = { project = "data_mesh_plt", purpose = "terraform-state" }
}

resource "azurerm_storage_account" "tfstate" {
  name                            = "dmplttfstate"
  resource_group_name             = azurerm_resource_group.tfstate.name
  location                        = azurerm_resource_group.tfstate.location
  account_tier                    = "Standard"
  account_replication_type        = "LRS"
  min_tls_version                 = "TLS1_2"
  allow_nested_items_to_be_public = false
  tags                            = { project = "data_mesh_plt", purpose = "terraform-state" }
}

resource "azurerm_storage_container" "tfstate" {
  name                  = "tfstate"
  storage_account_id    = azurerm_storage_account.tfstate.id
  container_access_type = "private"
}

output "backend_resource_group_name" { value = azurerm_resource_group.tfstate.name }
output "backend_storage_account_name" { value = azurerm_storage_account.tfstate.name }
output "backend_container_name" { value = azurerm_storage_container.tfstate.name }
