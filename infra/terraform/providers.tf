provider "azurerm" {
  features {}
  subscription_id = var.subscription_id
  tenant_id       = var.tenant_id
}

provider "azuread" {
  tenant_id = var.tenant_id
}

# Account-level Databricks: metastore + assignment. Authenticated as dmplt-admin
# (must be a Databricks account admin — see infra/terraform/README.md bootstrap).
provider "databricks" {
  alias      = "account"
  host       = "https://accounts.azuredatabricks.net"
  account_id = var.databricks_account_id
}

# Workspace-level Databricks: storage credential, external locations, catalogs, grants.
provider "databricks" {
  alias                       = "workspace"
  host                        = module.databricks_workspace.workspace_url
  azure_workspace_resource_id = module.databricks_workspace.workspace_id
}
