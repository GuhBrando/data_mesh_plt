# Reads the platform stack outputs. Because these values live in committed remote
# state, they are KNOWN at plan time — which is what lets the databricks.workspace
# provider below be configured without the chicken-and-egg the monolith had.
data "terraform_remote_state" "platform" {
  backend = "azurerm"
  config = {
    resource_group_name  = "dmplt-tfstate-rg"
    storage_account_name = "dmplttfstate"
    container_name       = "tfstate"
    key                  = "platform.tfstate"
  }
}
