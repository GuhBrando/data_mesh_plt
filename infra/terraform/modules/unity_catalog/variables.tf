variable "location" { type = string }
variable "workspace_id" { type = string }
variable "workspace_numeric_id" {
  type        = string
  description = "Numeric Databricks workspace id for metastore assignment."
}
variable "access_connector_id" { type = string }
variable "storage_account_name" { type = string }
variable "container_names" {
  type        = map(string)
  description = "Map of catalog key (dev/pre/pro) to container name."
}
variable "catalog_owner" {
  type        = string
  description = "Principal (application/client id of dmplt-admin) that owns the catalogs."
}
variable "devops_principal" {
  type        = string
  description = "Principal (application/client id of dmplt-devops) granted automation privileges."
}
