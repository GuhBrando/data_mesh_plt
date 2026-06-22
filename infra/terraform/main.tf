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
