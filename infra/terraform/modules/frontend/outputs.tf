output "default_host_name" { value = azurerm_static_web_app.frontend.default_host_name }
output "api_key" {
  value     = azurerm_static_web_app.frontend.api_key
  sensitive = true
}
