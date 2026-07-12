output "storage_account_id" { value = azurerm_storage_account.data.id }
output "storage_account_name" { value = azurerm_storage_account.data.name }
output "dfs_endpoint" { value = azurerm_storage_account.data.primary_dfs_endpoint }
output "container_names" {
  value = { for k, c in azurerm_storage_container.catalog : k => c.name }
}
