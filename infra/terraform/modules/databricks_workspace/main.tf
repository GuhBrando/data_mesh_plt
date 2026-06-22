resource "azurerm_databricks_workspace" "adb" {
  name                = "dmplt-adb"
  resource_group_name = var.resource_group_name
  location            = var.location
  sku                 = "premium" # required for Unity Catalog
  tags                = var.tags
  # No VNet injection (default) — avoids NAT Gateway cost.
}

# Managed identity used as the Unity Catalog storage credential.
resource "azurerm_databricks_access_connector" "uc" {
  name                = "dmplt-adb-connector"
  resource_group_name = var.resource_group_name
  location            = var.location
  identity {
    type = "SystemAssigned"
  }
  tags = var.tags
}
