locals {
  catalogs = ["dev", "pre", "pro"]
}

# Module blocks are wired in their respective tasks.

module "identities" {
  source          = "./modules/identities"
  github_repo     = var.github_repo
  subscription_id = var.subscription_id
}

module "core" {
  source   = "./modules/core"
  location = var.location
  tags     = var.tags
}

module "backend_app" {
  source                       = "./modules/backend_app"
  resource_group_name          = module.core.resource_group_name
  container_app_environment_id = module.core.container_app_environment_id
  acr_login_server             = module.core.acr_login_server
  acr_name                     = module.core.acr_name
  tags                         = var.tags
}

module "frontend" {
  source              = "./modules/frontend"
  resource_group_name = module.core.resource_group_name
  location            = var.location
  tags                = var.tags
}
