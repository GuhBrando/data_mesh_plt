locals {
  platform = data.terraform_remote_state.platform.outputs
}

# Register dmplt-admin (created in the platform stack as an Azure AD SP) as an
# account-level service principal in Databricks. This pre-registers the automation
# identity so it shows up in the Account Console.
#
# IMPORTANT: the **account admin** role itself CANNOT be granted via Terraform — the
# databricks provider's access_control_rule_set supports only marketplace.admin,
# billing.admin and tagPolicy.* roles at account scope (there is no `account_admin`).
# After this applies, flip the "Account admin" toggle on dmplt-admin in the Account
# Console (User management → Service principals) — an additive, one-time step.
resource "databricks_service_principal" "admin" {
  provider       = databricks.account
  application_id = local.platform.admin_client_id
  display_name   = "dmplt-admin"
}

# Assign dmplt-admin to the workspace as ADMIN. Account admin (granted separately
# via grant-account-admin.sh) lets it manage account-level objects like the
# metastore; this gives it the WORKSPACE-level access needed for storage
# credentials, external locations and catalogs. Unlike account_admin, this one IS
# expressible in Terraform.
resource "databricks_mws_permission_assignment" "admin_workspace" {
  provider     = databricks.account
  workspace_id = local.platform.workspace_numeric_id
  principal_id = databricks_service_principal.admin.id
  permissions  = ["ADMIN"]
}
