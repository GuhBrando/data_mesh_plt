# --- Metastore (account-level, no root storage) ---
resource "databricks_metastore" "this" {
  provider      = databricks.account
  name          = "dmplt-metastore-${var.location}"
  region        = var.location
  force_destroy = false
}

resource "databricks_metastore_assignment" "this" {
  provider     = databricks.account
  metastore_id = databricks_metastore.this.id
  workspace_id = var.workspace_numeric_id
}

# --- Storage credential via Access Connector (workspace-level) ---
resource "databricks_storage_credential" "this" {
  provider = databricks.workspace
  name     = "dmplt-uc-credential"
  azure_managed_identity {
    access_connector_id = var.access_connector_id
  }
  depends_on = [databricks_metastore_assignment.this]
}

# --- One external location + catalog per environment ---
resource "databricks_external_location" "this" {
  provider        = databricks.workspace
  for_each        = var.container_names
  name            = "dmplt-loc-${each.key}"
  url             = "abfss://${each.value}@${var.storage_account_name}.dfs.core.windows.net/"
  credential_name = databricks_storage_credential.this.name
}

resource "databricks_catalog" "this" {
  provider     = databricks.workspace
  for_each     = var.container_names
  name         = upper(each.key) # DEV / PRE / PRO
  storage_root = databricks_external_location.this[each.key].url
  owner        = var.catalog_owner
  comment      = "Managed by Terraform — ${upper(each.key)} environment"
}

resource "databricks_service_principal" "devops" {
  provider       = databricks.account
  application_id = var.devops_principal
  display_name   = "dmplt-devops"
}

# devops automation privileges on each catalog.
resource "databricks_grants" "devops" {
  provider   = databricks.workspace
  for_each   = databricks_catalog.this
  catalog    = each.value.name
  depends_on = [databricks_service_principal.devops]
  grant {
    principal  = var.devops_principal
    privileges = ["USE_CATALOG", "USE_SCHEMA", "CREATE_SCHEMA"]
  }
}
