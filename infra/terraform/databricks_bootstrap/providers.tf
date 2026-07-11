# Authenticated via Azure CLI as the logged-in identity, which must be a Databricks
# account admin. An Azure AD Global Administrator is one implicitly — so this stack
# is the ONE place a human Global Admin is required. Run it once; afterwards the
# data_plane stack authenticates purely as the dmplt-admin service principal.
provider "databricks" {
  alias           = "account"
  host            = "https://accounts.azuredatabricks.net"
  account_id      = var.databricks_account_id
  azure_tenant_id = var.tenant_id
  auth_type       = "azure-cli"
}
