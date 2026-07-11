terraform {
  backend "azurerm" {
    resource_group_name  = "dmplt-tfstate-rg"
    storage_account_name = "dmplttfstate"
    container_name       = "tfstate"
    key                  = "platform.tfstate"
    # Access state via Azure AD (Storage Blob Data Contributor) instead of
    # account keys, so the CI service principal doesn't need listKeys rights.
    use_azuread_auth     = true
  }
}
