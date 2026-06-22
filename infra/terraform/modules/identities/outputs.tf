output "admin_object_id" { value = azuread_service_principal.admin.object_id }
output "admin_client_id" { value = azuread_application.admin.client_id }
output "admin_client_secret" {
  value     = azuread_application_password.admin.value
  sensitive = true
}
output "devops_object_id" { value = azuread_service_principal.devops.object_id }
output "devops_client_id" { value = azuread_application.devops.client_id }
output "devops_client_secret" {
  value     = azuread_application_password.devops.value
  sensitive = true
}
