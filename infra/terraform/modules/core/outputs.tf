output "resource_group_name" { value = azurerm_resource_group.main.name }
output "resource_group_id" { value = azurerm_resource_group.main.id }
output "acr_login_server" { value = azurerm_container_registry.main.login_server }
output "acr_name" { value = azurerm_container_registry.main.name }
output "container_app_environment_id" { value = azurerm_container_app_environment.main.id }
output "location" { value = azurerm_resource_group.main.location }
