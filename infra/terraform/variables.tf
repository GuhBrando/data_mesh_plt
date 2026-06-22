variable "subscription_id" {
  type        = string
  description = "Azure subscription ID."
}

variable "tenant_id" {
  type        = string
  description = "Azure AD tenant ID."
}

variable "location" {
  type        = string
  default     = "westus2"
  description = "Azure region for all resources."
}

variable "databricks_account_id" {
  type        = string
  sensitive   = true
  description = "Databricks Account ID (from the Account Console)."
}

variable "github_repo" {
  type        = string
  default     = "GuhBrando/data_mesh_plt"
  description = "owner/repo used as the OIDC subject for the devops SP."
}

variable "tags" {
  type    = map(string)
  default = { project = "data_mesh_plt", managed_by = "terraform" }
}
