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
