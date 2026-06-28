resource "azurerm_databricks_workspace" "adb" {
  name                = "dmplt-adb"
  resource_group_name = var.resource_group_name
  location            = var.location
  sku                 = "premium" # required for Unity Catalog
  tags                = var.tags

  # No VNet injection (managed VNet). Secure Cluster Connectivity is
  # disabled (no_public_ip = false) so Databricks does NOT provision a
  # NAT Gateway in the managed resource group (~$32/mo fixed). Cluster
  # nodes get public IPs instead, billed only while clusters run.
  # Note: changing no_public_ip forces workspace recreation.
  custom_parameters {
    no_public_ip = false
  }
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
