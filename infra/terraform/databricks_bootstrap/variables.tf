variable "databricks_account_id" {
  type        = string
  sensitive   = true
  description = "Databricks Account ID (from the Account Console)."
}

variable "tenant_id" {
  type        = string
  description = "Azure AD tenant ID — used for Azure CLI auth against the account API."
}
