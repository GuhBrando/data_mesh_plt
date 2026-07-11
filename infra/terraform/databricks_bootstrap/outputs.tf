output "admin_service_principal_id" {
  value       = databricks_service_principal.admin.acl_principal_id
  description = "ACL principal id of the dmplt-admin account service principal."
}
