# Static Web Apps Free tier is only available in select regions; westus2 maps to "West US 2".
resource "azurerm_static_web_app" "frontend" {
  name                = "dmplt-stapp-frontend"
  resource_group_name = var.resource_group_name
  location            = var.location
  sku_tier            = "Free"
  sku_size            = "Free"
  tags                = var.tags
}
