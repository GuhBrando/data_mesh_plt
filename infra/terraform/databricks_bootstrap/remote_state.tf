# Reads the platform stack outputs to get the dmplt-admin SP's application id.
data "terraform_remote_state" "platform" {
  backend = "azurerm"
  config = {
    resource_group_name  = "dmplt-tfstate-rg"
    storage_account_name = "dmplttfstate"
    container_name       = "tfstate"
    key                  = "platform.tfstate"
  }
}
