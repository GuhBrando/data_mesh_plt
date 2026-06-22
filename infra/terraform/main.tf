locals {
  catalogs = ["dev", "pre", "pro"]
}

# Module blocks are wired in their respective tasks.

module "identities" {
  source          = "./modules/identities"
  github_repo     = var.github_repo
  subscription_id = var.subscription_id
}

module "core" {
  source   = "./modules/core"
  location = var.location
  tags     = var.tags
}

module "backend_app" {
  source                       = "./modules/backend_app"
  resource_group_name          = module.core.resource_group_name
  container_app_environment_id = module.core.container_app_environment_id
  acr_login_server             = module.core.acr_login_server
  acr_name                     = module.core.acr_name
  tags                         = var.tags
}

module "frontend" {
  source              = "./modules/frontend"
  resource_group_name = module.core.resource_group_name
  location            = var.location
  tags                = var.tags
}

module "storage" {
  source              = "./modules/storage"
  resource_group_name = module.core.resource_group_name
  location            = var.location
  tags                = var.tags
  containers          = local.catalogs
}

module "databricks_workspace" {
  source              = "./modules/databricks_workspace"
  resource_group_name = module.core.resource_group_name
  location            = var.location
  tags                = var.tags
}

# Access Connector managed identity → data plane access on dmpltsta.
resource "azurerm_role_assignment" "uc_storage" {
  scope                = module.storage.storage_account_id
  role_definition_name = "Storage Blob Data Contributor"
  principal_id         = module.databricks_workspace.access_connector_principal_id
}

module "unity_catalog" {
  source               = "./modules/unity_catalog"
  location             = var.location
  workspace_id         = module.databricks_workspace.workspace_id
  workspace_numeric_id = module.databricks_workspace.workspace_numeric_id
  access_connector_id  = module.databricks_workspace.access_connector_id
  storage_account_name = module.storage.storage_account_name
  container_names      = module.storage.container_names
  catalog_owner        = module.identities.admin_client_id
  devops_principal     = module.identities.devops_client_id

  providers = {
    databricks.account   = databricks.account
    databricks.workspace = databricks.workspace
  }
}
