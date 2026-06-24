terraform {
  backend "azurerm" {
    resource_group_name  = "dmplt-tfstate-rg"
    storage_account_name = "dmplttfstate"
    container_name       = "tfstate"
    key                  = "platform.tfstate"
  }
}
