locals {
  platform = data.terraform_remote_state.platform.outputs
}

module "unity_catalog" {
  source               = "../modules/unity_catalog"
  location             = local.platform.location
  workspace_id         = local.platform.workspace_id
  workspace_numeric_id = local.platform.workspace_numeric_id
  access_connector_id  = local.platform.access_connector_id
  storage_account_name = local.platform.storage_account_name
  container_names      = local.platform.container_names
  catalog_owner        = local.platform.admin_client_id
  devops_principal     = local.platform.devops_client_id

  providers = {
    databricks.account   = databricks.account
    databricks.workspace = databricks.workspace
  }
}
