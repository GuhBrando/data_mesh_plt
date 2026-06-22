output "admin_client_id" { value = module.identities.admin_client_id }
output "admin_client_secret" {
  value     = module.identities.admin_client_secret
  sensitive = true
}
output "devops_client_id" { value = module.identities.devops_client_id }
output "devops_client_secret" {
  value     = module.identities.devops_client_secret
  sensitive = true
}
output "catalog_names" { value = module.unity_catalog.catalog_names }
output "databricks_workspace_url" { value = module.databricks_workspace.workspace_url }
