# Account-level Databricks: metastore + assignment. Authenticated as the dmplt-admin
# Azure service principal, whose id/secret come from the platform stack's remote
# state. dmplt-admin must be a Databricks ACCOUNT ADMIN — a one-time bootstrap grant
# performed by a Global Administrator (see README step 2). This makes the stack
# reproducible across machines and CI (no human az session required).
provider "databricks" {
  alias               = "account"
  host                = "https://accounts.azuredatabricks.net"
  account_id          = var.databricks_account_id
  azure_client_id     = local.platform.admin_client_id
  azure_client_secret = local.platform.admin_client_secret
  azure_tenant_id     = var.tenant_id
}

# Workspace-level Databricks: storage credential, external locations, catalogs, grants.
# Same dmplt-admin SP — an account admin can operate on the workspace as well.
provider "databricks" {
  alias                       = "workspace"
  host                        = local.platform.workspace_url
  azure_workspace_resource_id = local.platform.workspace_id
  azure_client_id             = local.platform.admin_client_id
  azure_client_secret         = local.platform.admin_client_secret
  azure_tenant_id             = var.tenant_id
}
