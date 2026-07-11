data "azuread_client_config" "current" {}

# Owners are seeded at creation but reconciled OUT of Terraform: grant-ci-permissions.sh
# adds dmplt-devops as owner of every app/SP here (including itself — a self-reference
# HCL cannot express), and `current.object_id` differs between human and CI runs, so
# managing the list here would strip one owner on every alternate apply.

# --- dmplt-admin: governance (Databricks account/metastore admin, catalog owner) ---
resource "azuread_application" "admin" {
  display_name = "dmplt-admin"
  owners       = [data.azuread_client_config.current.object_id]

  lifecycle {
    ignore_changes = [owners]
  }
}

resource "azuread_service_principal" "admin" {
  client_id = azuread_application.admin.client_id
  owners    = [data.azuread_client_config.current.object_id]

  lifecycle {
    ignore_changes = [owners]
  }
}

resource "azuread_application_password" "admin" {
  application_id = azuread_application.admin.id
  display_name   = "terraform-managed"
}

# --- dmplt-devops: CI/CD automation (Terraform runner via OIDC) ---
resource "azuread_application" "devops" {
  display_name = "dmplt-devops"
  owners       = [data.azuread_client_config.current.object_id]

  lifecycle {
    ignore_changes = [owners]
  }
}

resource "azuread_service_principal" "devops" {
  client_id = azuread_application.devops.client_id
  owners    = [data.azuread_client_config.current.object_id]

  lifecycle {
    ignore_changes = [owners]
  }
}

# OIDC federated credential so GitHub Actions assumes dmplt-devops without a secret.
resource "azuread_application_federated_identity_credential" "devops_main" {
  application_id = azuread_application.devops.id
  display_name   = "github-main"
  audiences      = ["api://AzureADTokenExchange"]
  issuer         = "https://token.actions.githubusercontent.com"
  subject        = "repo:${var.github_repo}:ref:refs/heads/main"
}

resource "azuread_application_federated_identity_credential" "devops_pr" {
  application_id = azuread_application.devops.id
  display_name   = "github-pr"
  audiences      = ["api://AzureADTokenExchange"]
  issuer         = "https://token.actions.githubusercontent.com"
  subject        = "repo:${var.github_repo}:pull_request"
}

# devops needs Contributor on the subscription to manage infra (scope tightened to RGs post-import if desired).
resource "azurerm_role_assignment" "devops_contributor" {
  scope                = "/subscriptions/${var.subscription_id}"
  role_definition_name = "Contributor"
  principal_id         = azuread_service_principal.devops.object_id
}
