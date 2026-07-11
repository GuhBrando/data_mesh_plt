variable "databricks_account_id" {
  type        = string
  sensitive   = true
  description = "Databricks Account ID (from the Account Console)."
}

variable "tenant_id" {
  type        = string
  description = "Azure AD tenant ID — used to authenticate the Databricks providers via Azure CLI."
}
