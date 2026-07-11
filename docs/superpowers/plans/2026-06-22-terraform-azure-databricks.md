# Terraform Azure Deploy + Databricks (Unity Catalog) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Migrate all Azure provisioning to Terraform (importing existing resources) and add a Databricks workspace with Unity Catalog (3 catalogs, dedicated ADLS Gen2 storage) governed by two Azure AD service principals.

**Architecture:** A single-environment Terraform root in `infra/terraform/` with focused modules (identities, core, backend_app, frontend, storage, databricks_workspace, unity_catalog), remote `azurerm` state, and a GitHub Actions workflow (`infra.yml`) that plans on PR and applies via OIDC. Existing Azure resources are imported (not recreated). The app image rollout stays in `cd.yml`; Terraform ignores image drift.

**Tech Stack:** Terraform (azurerm ~> 4.0, azuread ~> 3.0, databricks ~> 1.50), Azure (Container Apps, ACR, Static Web Apps, ADLS Gen2, Azure Databricks Premium), GitHub Actions OIDC.

## Global Constraints

- **Region:** `westus2` for ALL resources (single UC metastore is per-region).
- **Lowest cost is a determining factor**, balanced to not lose functionality: Databricks **Premium** SKU (required for UC) but **no VNet injection** (avoids ~$30/mo NAT Gateway); **no** clusters/SQL warehouses provisioned by Terraform; storage **Standard LRS** with HNS; ACR **Basic** (only fixed cost, ~$5/mo); Container App **min-replicas 0**; Static Web App **Free**; Log Analytics retention **30 days**; UC metastore **without root storage**.
- **Names (exact):** RG `dmplt-rg`, ACR `dmpltacr`, Container Apps Env `dmplt-cae`, backend Container App `dmplt-ca-backend`, Static Web App `dmplt-stapp-frontend`, Databricks workspace `dmplt-adb`, storage account `dmpltsta`, SPNs `dmplt-admin` and `dmplt-devops`, catalogs `DEV`/`PRE`/`PRO` (containers `dev`/`pre`/`pro`).
- **Existing resources are IMPORTED** — `terraform plan` after import MUST show zero destroy/replace on them.
- **No long-lived Azure secrets in GitHub** — CI auth via OIDC federated credential on `dmplt-devops`.
- **Per-task test cycle:** `terraform init -backend=false` → `terraform validate` → `terraform fmt -check -recursive` must all succeed. Real `import`/`apply` against live Azure is a runbook activity, NOT part of automated task validation.
- **Sensitive values** (SP secrets, `databricks_account_id`) are `sensitive` vars/outputs; never commit real values. `terraform.tfvars` is gitignored.

---

### Task 1: State backend bootstrap

**Files:**
- Create: `infra/terraform/bootstrap/main.tf`
- Create: `infra/terraform/bootstrap/README.md`
- Create: `infra/terraform/.gitignore`

**Interfaces:**
- Consumes: nothing.
- Produces: Storage Account `dmplttfstate` + container `tfstate` in RG `dmplt-tfstate-rg` (consumed by root `backend.tf` in Task 2).

- [ ] **Step 1: Create the gitignore**

Create `infra/terraform/.gitignore`:

```gitignore
.terraform/
*.tfstate
*.tfstate.*
*.tfplan
crash.log
*.auto.tfvars
terraform.tfvars
.terraform.lock.hcl
```

- [ ] **Step 2: Create the bootstrap config**

Create `infra/terraform/bootstrap/main.tf`:

```hcl
terraform {
  required_version = ">= 1.6"
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 4.0"
    }
  }
  # Local state on purpose: this bootstraps the remote backend itself.
}

provider "azurerm" {
  features {}
  subscription_id = var.subscription_id
}

variable "subscription_id" {
  type        = string
  description = "Azure subscription ID."
}

variable "location" {
  type    = string
  default = "westus2"
}

resource "azurerm_resource_group" "tfstate" {
  name     = "dmplt-tfstate-rg"
  location = var.location
  tags     = { project = "data_mesh_plt", purpose = "terraform-state" }
}

resource "azurerm_storage_account" "tfstate" {
  name                            = "dmplttfstate"
  resource_group_name             = azurerm_resource_group.tfstate.name
  location                        = azurerm_resource_group.tfstate.location
  account_tier                    = "Standard"
  account_replication_type        = "LRS"
  min_tls_version                 = "TLS1_2"
  allow_nested_items_to_be_public = false
  tags                            = { project = "data_mesh_plt", purpose = "terraform-state" }
}

resource "azurerm_storage_container" "tfstate" {
  name                  = "tfstate"
  storage_account_id    = azurerm_storage_account.tfstate.id
  container_access_type = "private"
}

output "backend_resource_group_name" { value = azurerm_resource_group.tfstate.name }
output "backend_storage_account_name" { value = azurerm_storage_account.tfstate.name }
output "backend_container_name" { value = azurerm_storage_container.tfstate.name }
```

- [ ] **Step 3: Create the bootstrap README**

Create `infra/terraform/bootstrap/README.md`:

```markdown
# Terraform State Backend Bootstrap

Run ONCE before initializing the root module. Creates the Azure Storage
Account that holds the remote Terraform state.

```bash
cd infra/terraform/bootstrap
az login
terraform init
terraform apply -var="subscription_id=<YOUR_SUBSCRIPTION_ID>"
```

Outputs feed the root `backend.tf`:
- resource group: `dmplt-tfstate-rg`
- storage account: `dmplttfstate`
- container: `tfstate`

State for this bootstrap stays LOCAL (it provisions the remote backend itself).
```

- [ ] **Step 4: Validate**

Run:
```bash
cd infra/terraform/bootstrap && terraform init -backend=false && terraform validate && terraform fmt -check
```
Expected: `Success! The configuration is valid.` and fmt prints nothing (exit 0).

- [ ] **Step 5: Commit**

```bash
git add infra/terraform/.gitignore infra/terraform/bootstrap/
git commit -m "feat(infra): terraform state backend bootstrap"
```

---

### Task 2: Root scaffolding (providers, backend, variables)

**Files:**
- Create: `infra/terraform/versions.tf`
- Create: `infra/terraform/providers.tf`
- Create: `infra/terraform/backend.tf`
- Create: `infra/terraform/variables.tf`
- Create: `infra/terraform/terraform.tfvars.example`
- Create: `infra/terraform/main.tf` (empty wiring placeholder with locals)

**Interfaces:**
- Consumes: bootstrap storage (Task 1) for backend.
- Produces: configured providers `azurerm`, `azuread`, `databricks.account`, `databricks.workspace`; root variables consumed by all modules.

- [ ] **Step 1: Create versions.tf**

Create `infra/terraform/versions.tf`:

```hcl
terraform {
  required_version = ">= 1.6"
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 4.0"
    }
    azuread = {
      source  = "hashicorp/azuread"
      version = "~> 3.0"
    }
    databricks = {
      source  = "databricks/databricks"
      version = "~> 1.50"
    }
  }
}
```

- [ ] **Step 2: Create backend.tf**

Create `infra/terraform/backend.tf`:

```hcl
terraform {
  backend "azurerm" {
    resource_group_name  = "dmplt-tfstate-rg"
    storage_account_name = "dmplttfstate"
    container_name       = "tfstate"
    key                  = "data_mesh_plt.tfstate"
  }
}
```

- [ ] **Step 3: Create variables.tf**

Create `infra/terraform/variables.tf`:

```hcl
variable "subscription_id" {
  type        = string
  description = "Azure subscription ID."
}

variable "tenant_id" {
  type        = string
  description = "Azure AD tenant ID."
}

variable "location" {
  type        = string
  default     = "westus2"
  description = "Azure region for all resources."
}

variable "databricks_account_id" {
  type        = string
  sensitive   = true
  description = "Databricks Account ID (from the Account Console)."
}

variable "github_repo" {
  type        = string
  default     = "GuhBrando/data_mesh_plt"
  description = "owner/repo used as the OIDC subject for the devops SP."
}

variable "tags" {
  type    = map(string)
  default = { project = "data_mesh_plt", managed_by = "terraform" }
}
```

- [ ] **Step 4: Create providers.tf**

Create `infra/terraform/providers.tf`:

```hcl
provider "azurerm" {
  features {}
  subscription_id = var.subscription_id
  tenant_id       = var.tenant_id
}

provider "azuread" {
  tenant_id = var.tenant_id
}

# Account-level Databricks: metastore + assignment. Authenticated as dmplt-admin
# (must be a Databricks account admin — see infra/terraform/README.md bootstrap).
provider "databricks" {
  alias      = "account"
  host       = "https://accounts.azuredatabricks.net"
  account_id = var.databricks_account_id
}

# Workspace-level Databricks: storage credential, external locations, catalogs, grants.
provider "databricks" {
  alias                       = "workspace"
  host                        = module.databricks_workspace.workspace_url
  azure_workspace_resource_id = module.databricks_workspace.workspace_id
}
```

- [ ] **Step 5: Create main.tf placeholder and tfvars example**

Create `infra/terraform/main.tf`:

```hcl
locals {
  catalogs = ["dev", "pre", "pro"]
}

# Module blocks are wired in their respective tasks.
```

Create `infra/terraform/terraform.tfvars.example`:

```hcl
subscription_id       = "00000000-0000-0000-0000-000000000000"
tenant_id             = "00000000-0000-0000-0000-000000000000"
databricks_account_id = "00000000-0000-0000-0000-000000000000"
location              = "westus2"
github_repo           = "GuhBrando/data_mesh_plt"
```

- [ ] **Step 6: Validate**

Run:
```bash
cd infra/terraform && terraform init -backend=false && terraform validate && terraform fmt -check -recursive
```
Expected: `Success! The configuration is valid.` (The `databricks.workspace` provider references `module.databricks_workspace` which doesn't exist yet — so temporarily comment out the `databricks.workspace` provider block for THIS validation, then restore it. Note this in the commit.)

Simpler: for this task, leave the `databricks.workspace` provider block commented out with a `# wired in Task 8` marker; uncomment in Task 8.

- [ ] **Step 7: Commit**

```bash
git add infra/terraform/versions.tf infra/terraform/providers.tf infra/terraform/backend.tf infra/terraform/variables.tf infra/terraform/main.tf infra/terraform/terraform.tfvars.example
git commit -m "feat(infra): terraform root scaffolding and providers"
```

---

### Task 3: Module `identities` (service principals dmplt-admin & dmplt-devops)

**Files:**
- Create: `infra/terraform/modules/identities/main.tf`
- Create: `infra/terraform/modules/identities/variables.tf`
- Create: `infra/terraform/modules/identities/outputs.tf`
- Modify: `infra/terraform/main.tf` (add module block)
- Modify: `infra/terraform/outputs.tf` (create; expose SP outputs)

**Interfaces:**
- Consumes: `var.tenant_id`, `var.subscription_id`, `var.github_repo`.
- Produces:
  - `module.identities.admin_object_id` (string) — dmplt-admin SP object id
  - `module.identities.admin_client_id` (string)
  - `module.identities.admin_client_secret` (string, sensitive)
  - `module.identities.devops_object_id` (string)
  - `module.identities.devops_client_id` (string)
  - `module.identities.devops_client_secret` (string, sensitive)

- [ ] **Step 1: Create module variables**

Create `infra/terraform/modules/identities/variables.tf`:

```hcl
variable "github_repo" {
  type        = string
  description = "owner/repo for the OIDC federated credential subject."
}

variable "subscription_id" {
  type = string
}
```

- [ ] **Step 2: Create module main**

Create `infra/terraform/modules/identities/main.tf`:

```hcl
data "azuread_client_config" "current" {}

# --- dmplt-admin: governance (Databricks account/metastore admin, catalog owner) ---
resource "azuread_application" "admin" {
  display_name = "dmplt-admin"
  owners       = [data.azuread_client_config.current.object_id]
}

resource "azuread_service_principal" "admin" {
  client_id = azuread_application.admin.client_id
  owners    = [data.azuread_client_config.current.object_id]
}

resource "azuread_application_password" "admin" {
  application_id = azuread_application.admin.id
  display_name   = "terraform-managed"
}

# --- dmplt-devops: CI/CD automation (Terraform runner via OIDC) ---
resource "azuread_application" "devops" {
  display_name = "dmplt-devops"
  owners       = [data.azuread_client_config.current.object_id]
}

resource "azuread_service_principal" "devops" {
  client_id = azuread_application.devops.client_id
  owners    = [data.azuread_client_config.current.object_id]
}

resource "azuread_application_password" "devops" {
  application_id = azuread_application.devops.id
  display_name   = "terraform-managed"
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
```

- [ ] **Step 3: Create module outputs**

Create `infra/terraform/modules/identities/outputs.tf`:

```hcl
output "admin_object_id" { value = azuread_service_principal.admin.object_id }
output "admin_client_id" { value = azuread_application.admin.client_id }
output "admin_client_secret" {
  value     = azuread_application_password.admin.value
  sensitive = true
}
output "devops_object_id" { value = azuread_service_principal.devops.object_id }
output "devops_client_id" { value = azuread_application.devops.client_id }
output "devops_client_secret" {
  value     = azuread_application_password.devops.value
  sensitive = true
}
```

- [ ] **Step 4: Wire module + root outputs**

In `infra/terraform/main.tf` append:

```hcl
module "identities" {
  source          = "./modules/identities"
  github_repo     = var.github_repo
  subscription_id = var.subscription_id
}
```

Create `infra/terraform/outputs.tf`:

```hcl
output "admin_client_id" { value = module.identities.admin_client_id }
output "admin_client_secret" {
  value     = module.identities.admin_client_secret
  sensitive = true
}
output "devops_client_id" { value = module.identities.devops_client_id }
output "devops_client_secret" {
  value     = module.identities.devops_client_secret
  sensitive = true
}
```

- [ ] **Step 5: Validate**

Run:
```bash
cd infra/terraform && terraform init -backend=false && terraform validate && terraform fmt -check -recursive
```
Expected: `Success! The configuration is valid.`

- [ ] **Step 6: Commit**

```bash
git add infra/terraform/modules/identities/ infra/terraform/main.tf infra/terraform/outputs.tf
git commit -m "feat(infra): identities module (dmplt-admin and dmplt-devops SPNs)"
```

---

### Task 4: Module `core` (RG, ACR, Log Analytics, Container Apps Env) — import targets

**Files:**
- Create: `infra/terraform/modules/core/main.tf`
- Create: `infra/terraform/modules/core/variables.tf`
- Create: `infra/terraform/modules/core/outputs.tf`
- Modify: `infra/terraform/main.tf`

**Interfaces:**
- Consumes: `var.location`, `var.tags`.
- Produces:
  - `module.core.resource_group_name` (string)
  - `module.core.resource_group_id` (string)
  - `module.core.acr_login_server` (string)
  - `module.core.container_app_environment_id` (string)

- [ ] **Step 1: Create module variables**

Create `infra/terraform/modules/core/variables.tf`:

```hcl
variable "location" { type = string }
variable "tags" { type = map(string) }
```

- [ ] **Step 2: Create module main**

Create `infra/terraform/modules/core/main.tf`:

```hcl
resource "azurerm_resource_group" "main" {
  name     = "dmplt-rg"
  location = var.location
  tags     = var.tags
}

resource "azurerm_container_registry" "main" {
  name                = "dmpltacr"
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  sku                 = "Basic"
  admin_enabled       = true
  tags                = var.tags
}

resource "azurerm_log_analytics_workspace" "main" {
  name                = "dmplt-law"
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  sku                 = "PerGB2018"
  retention_in_days   = 30
  tags                = var.tags
}

resource "azurerm_container_app_environment" "main" {
  name                       = "dmplt-cae"
  resource_group_name        = azurerm_resource_group.main.name
  location                   = azurerm_resource_group.main.location
  log_analytics_workspace_id = azurerm_log_analytics_workspace.main.id
  tags                       = var.tags
}
```

- [ ] **Step 3: Create module outputs**

Create `infra/terraform/modules/core/outputs.tf`:

```hcl
output "resource_group_name" { value = azurerm_resource_group.main.name }
output "resource_group_id" { value = azurerm_resource_group.main.id }
output "acr_login_server" { value = azurerm_container_registry.main.login_server }
output "acr_name" { value = azurerm_container_registry.main.name }
output "container_app_environment_id" { value = azurerm_container_app_environment.main.id }
output "location" { value = azurerm_resource_group.main.location }
```

- [ ] **Step 4: Wire module**

In `infra/terraform/main.tf` append:

```hcl
module "core" {
  source   = "./modules/core"
  location = var.location
  tags     = var.tags
}
```

- [ ] **Step 5: Validate**

Run:
```bash
cd infra/terraform && terraform init -backend=false && terraform validate && terraform fmt -check -recursive
```
Expected: `Success! The configuration is valid.`

- [ ] **Step 6: Commit**

```bash
git add infra/terraform/modules/core/ infra/terraform/main.tf
git commit -m "feat(infra): core module (RG, ACR, Log Analytics, Container Apps Env)"
```

---

### Task 5: Module `backend_app` (Container App, ignore image drift) — import target

**Files:**
- Create: `infra/terraform/modules/backend_app/main.tf`
- Create: `infra/terraform/modules/backend_app/variables.tf`
- Create: `infra/terraform/modules/backend_app/outputs.tf`
- Modify: `infra/terraform/main.tf`

**Interfaces:**
- Consumes: `module.core.container_app_environment_id`, `module.core.resource_group_name`, `module.core.acr_login_server`, `module.core.acr_name`.
- Produces: `module.backend_app.fqdn` (string).

- [ ] **Step 1: Create module variables**

Create `infra/terraform/modules/backend_app/variables.tf`:

```hcl
variable "resource_group_name" { type = string }
variable "container_app_environment_id" { type = string }
variable "acr_login_server" { type = string }
variable "acr_name" { type = string }
variable "tags" { type = map(string) }
```

- [ ] **Step 2: Create module main**

Create `infra/terraform/modules/backend_app/main.tf`:

```hcl
data "azurerm_container_registry" "acr" {
  name                = var.acr_name
  resource_group_name = var.resource_group_name
}

resource "azurerm_container_app" "backend" {
  name                         = "dmplt-ca-backend"
  resource_group_name          = var.resource_group_name
  container_app_environment_id = var.container_app_environment_id
  revision_mode                = "Single"
  tags                         = var.tags

  registry {
    server               = var.acr_login_server
    username             = data.azurerm_container_registry.acr.admin_username
    password_secret_name = "acr-password"
  }

  secret {
    name  = "acr-password"
    value = data.azurerm_container_registry.acr.admin_password
  }

  ingress {
    external_enabled = true
    target_port      = 8000
    traffic_weight {
      latest_revision = true
      percentage      = 100
    }
  }

  template {
    min_replicas = 0
    max_replicas = 2

    container {
      name   = "backend"
      image  = "${var.acr_login_server}/backend:latest"
      cpu    = 0.25
      memory = "0.5Gi"
    }
  }

  lifecycle {
    # Image rollout is handled by cd.yml (az containerapp update) per release tag.
    ignore_changes = [template[0].container[0].image]
  }
}
```

- [ ] **Step 3: Create module outputs**

Create `infra/terraform/modules/backend_app/outputs.tf`:

```hcl
output "fqdn" { value = azurerm_container_app.backend.ingress[0].fqdn }
```

- [ ] **Step 4: Wire module**

In `infra/terraform/main.tf` append:

```hcl
module "backend_app" {
  source                       = "./modules/backend_app"
  resource_group_name          = module.core.resource_group_name
  container_app_environment_id = module.core.container_app_environment_id
  acr_login_server             = module.core.acr_login_server
  acr_name                     = module.core.acr_name
  tags                         = var.tags
}
```

- [ ] **Step 5: Validate**

Run:
```bash
cd infra/terraform && terraform init -backend=false && terraform validate && terraform fmt -check -recursive
```
Expected: `Success! The configuration is valid.`

- [ ] **Step 6: Commit**

```bash
git add infra/terraform/modules/backend_app/ infra/terraform/main.tf
git commit -m "feat(infra): backend_app module (Container App, ignore image drift)"
```

---

### Task 6: Module `frontend` (Static Web App) — import target

**Files:**
- Create: `infra/terraform/modules/frontend/main.tf`
- Create: `infra/terraform/modules/frontend/variables.tf`
- Create: `infra/terraform/modules/frontend/outputs.tf`
- Modify: `infra/terraform/main.tf`

**Interfaces:**
- Consumes: `module.core.resource_group_name`, `var.location`, `var.tags`.
- Produces: `module.frontend.default_host_name` (string), `module.frontend.api_key` (string, sensitive).

- [ ] **Step 1: Create module variables**

Create `infra/terraform/modules/frontend/variables.tf`:

```hcl
variable "resource_group_name" { type = string }
variable "location" { type = string }
variable "tags" { type = map(string) }
```

- [ ] **Step 2: Create module main**

Create `infra/terraform/modules/frontend/main.tf`:

```hcl
# Static Web Apps Free tier is only available in select regions; westus2 maps to "West US 2".
resource "azurerm_static_web_app" "frontend" {
  name                = "dmplt-stapp-frontend"
  resource_group_name = var.resource_group_name
  location            = var.location
  sku_tier            = "Free"
  sku_size            = "Free"
  tags                = var.tags
}
```

- [ ] **Step 3: Create module outputs**

Create `infra/terraform/modules/frontend/outputs.tf`:

```hcl
output "default_host_name" { value = azurerm_static_web_app.frontend.default_host_name }
output "api_key" {
  value     = azurerm_static_web_app.frontend.api_key
  sensitive = true
}
```

- [ ] **Step 4: Wire module**

In `infra/terraform/main.tf` append:

```hcl
module "frontend" {
  source              = "./modules/frontend"
  resource_group_name = module.core.resource_group_name
  location            = var.location
  tags                = var.tags
}
```

- [ ] **Step 5: Validate**

Run:
```bash
cd infra/terraform && terraform init -backend=false && terraform validate && terraform fmt -check -recursive
```
Expected: `Success! The configuration is valid.`

- [ ] **Step 6: Commit**

```bash
git add infra/terraform/modules/frontend/ infra/terraform/main.tf
git commit -m "feat(infra): frontend module (Static Web App, Free tier)"
```

---

### Task 7: Module `storage` (ADLS Gen2 dmpltsta + 3 containers)

**Files:**
- Create: `infra/terraform/modules/storage/main.tf`
- Create: `infra/terraform/modules/storage/variables.tf`
- Create: `infra/terraform/modules/storage/outputs.tf`
- Modify: `infra/terraform/main.tf`

**Interfaces:**
- Consumes: `module.core.resource_group_name`, `var.location`, `var.tags`, `local.catalogs`.
- Produces:
  - `module.storage.storage_account_id` (string)
  - `module.storage.storage_account_name` (string)
  - `module.storage.dfs_endpoint` (string) — e.g. `https://dmpltsta.dfs.core.windows.net/`
  - `module.storage.container_names` (map(string)) — keyed by `dev`/`pre`/`pro`

- [ ] **Step 1: Create module variables**

Create `infra/terraform/modules/storage/variables.tf`:

```hcl
variable "resource_group_name" { type = string }
variable "location" { type = string }
variable "tags" { type = map(string) }
variable "containers" {
  type        = list(string)
  description = "Container names, one per catalog (dev/pre/pro)."
}
```

- [ ] **Step 2: Create module main**

Create `infra/terraform/modules/storage/main.tf`:

```hcl
resource "azurerm_storage_account" "data" {
  name                            = "dmpltsta"
  resource_group_name             = var.resource_group_name
  location                        = var.location
  account_tier                    = "Standard"
  account_replication_type        = "LRS"
  account_kind                    = "StorageV2"
  is_hns_enabled                  = true
  min_tls_version                 = "TLS1_2"
  allow_nested_items_to_be_public = false
  tags                            = var.tags
}

resource "azurerm_storage_container" "catalog" {
  for_each              = toset(var.containers)
  name                  = each.value
  storage_account_id    = azurerm_storage_account.data.id
  container_access_type = "private"
}
```

- [ ] **Step 3: Create module outputs**

Create `infra/terraform/modules/storage/outputs.tf`:

```hcl
output "storage_account_id" { value = azurerm_storage_account.data.id }
output "storage_account_name" { value = azurerm_storage_account.data.name }
output "dfs_endpoint" { value = azurerm_storage_account.data.primary_dfs_endpoint }
output "container_names" {
  value = { for k, c in azurerm_storage_container.catalog : k => c.name }
}
```

- [ ] **Step 4: Wire module**

In `infra/terraform/main.tf` append:

```hcl
module "storage" {
  source              = "./modules/storage"
  resource_group_name = module.core.resource_group_name
  location            = var.location
  tags                = var.tags
  containers          = local.catalogs
}
```

- [ ] **Step 5: Validate**

Run:
```bash
cd infra/terraform && terraform init -backend=false && terraform validate && terraform fmt -check -recursive
```
Expected: `Success! The configuration is valid.`

- [ ] **Step 6: Commit**

```bash
git add infra/terraform/modules/storage/ infra/terraform/main.tf
git commit -m "feat(infra): storage module (ADLS Gen2 dmpltsta + dev/pre/pro containers)"
```

---

### Task 8: Module `databricks_workspace` (dmplt-adb Premium + Access Connector)

**Files:**
- Create: `infra/terraform/modules/databricks_workspace/main.tf`
- Create: `infra/terraform/modules/databricks_workspace/variables.tf`
- Create: `infra/terraform/modules/databricks_workspace/outputs.tf`
- Modify: `infra/terraform/main.tf`
- Modify: `infra/terraform/providers.tf` (uncomment `databricks.workspace`)

**Interfaces:**
- Consumes: `module.core.resource_group_name`, `var.location`, `var.tags`, `module.storage.storage_account_id`.
- Produces:
  - `module.databricks_workspace.workspace_id` (string) — Azure resource ID
  - `module.databricks_workspace.workspace_url` (string) — `https://<host>`
  - `module.databricks_workspace.access_connector_id` (string)
  - `module.databricks_workspace.access_connector_principal_id` (string)

- [ ] **Step 1: Create module variables**

Create `infra/terraform/modules/databricks_workspace/variables.tf`:

```hcl
variable "resource_group_name" { type = string }
variable "location" { type = string }
variable "tags" { type = map(string) }
```

- [ ] **Step 2: Create module main**

Create `infra/terraform/modules/databricks_workspace/main.tf`:

```hcl
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
```

- [ ] **Step 3: Create module outputs**

Create `infra/terraform/modules/databricks_workspace/outputs.tf`:

```hcl
output "workspace_id" { value = azurerm_databricks_workspace.adb.id }
output "workspace_url" { value = "https://${azurerm_databricks_workspace.adb.workspace_url}" }
output "access_connector_id" { value = azurerm_databricks_access_connector.uc.id }
output "access_connector_principal_id" {
  value = azurerm_databricks_access_connector.uc.identity[0].principal_id
}
```

- [ ] **Step 4: Wire module + grant storage access + uncomment workspace provider**

In `infra/terraform/main.tf` append:

```hcl
module "databricks_workspace" {
  source              = "./modules/databricks_workspace"
  resource_group_name = module.core.resource_group_name
  location            = var.location
  tags                = var.tags
}

# Access Connector managed identity → data plane access on dmpltsta.
resource "azurerm_role_assignment" "uc_storage" {
  scope                = module.storage.storage_account_id
  role_definition_name = "Storage Blob Data Contributor"
  principal_id         = module.databricks_workspace.access_connector_principal_id
}
```

In `infra/terraform/providers.tf`, uncomment the `databricks.workspace` provider block created in Task 2.

- [ ] **Step 5: Validate**

Run:
```bash
cd infra/terraform && terraform init -backend=false && terraform validate && terraform fmt -check -recursive
```
Expected: `Success! The configuration is valid.`

- [ ] **Step 6: Commit**

```bash
git add infra/terraform/modules/databricks_workspace/ infra/terraform/main.tf infra/terraform/providers.tf
git commit -m "feat(infra): databricks_workspace module (dmplt-adb + Access Connector)"
```

---

### Task 9: Module `unity_catalog` (metastore, credential, external locations, catalogs, grants)

**Files:**
- Create: `infra/terraform/modules/unity_catalog/main.tf`
- Create: `infra/terraform/modules/unity_catalog/variables.tf`
- Create: `infra/terraform/modules/unity_catalog/outputs.tf`
- Modify: `infra/terraform/main.tf`

**Interfaces:**
- Consumes: `var.location`, `module.databricks_workspace.workspace_id`, `module.databricks_workspace.access_connector_id`, `module.storage.storage_account_name`, `module.storage.container_names`, `module.identities.admin_client_id` (catalog owner), `module.identities.devops_object_id`/`devops_client_id`. Providers `databricks.account` and `databricks.workspace`.
- Produces: `module.unity_catalog.catalog_names` (map) — keyed `dev`/`pre`/`pro`.

- [ ] **Step 1: Create module variables**

Create `infra/terraform/modules/unity_catalog/variables.tf`:

```hcl
variable "location" { type = string }
variable "workspace_id" { type = string }
variable "access_connector_id" { type = string }
variable "storage_account_name" { type = string }
variable "container_names" {
  type        = map(string)
  description = "Map of catalog key (dev/pre/pro) to container name."
}
variable "catalog_owner" {
  type        = string
  description = "Principal (application/client id of dmplt-admin) that owns the catalogs."
}
variable "devops_principal" {
  type        = string
  description = "Principal (application/client id of dmplt-devops) granted automation privileges."
}
```

- [ ] **Step 2: Create module main**

Create `infra/terraform/modules/unity_catalog/main.tf`:

```hcl
# --- Metastore (account-level, no root storage) ---
resource "databricks_metastore" "this" {
  provider      = databricks.account
  name          = "dmplt-metastore-${var.location}"
  region        = var.location
  force_destroy = false
}

resource "databricks_metastore_assignment" "this" {
  provider     = databricks.account
  metastore_id = databricks_metastore.this.id
  workspace_id = element(split("/", var.workspace_id), length(split("/", var.workspace_id)) - 1)
}

# --- Storage credential via Access Connector (workspace-level) ---
resource "databricks_storage_credential" "this" {
  provider = databricks.workspace
  name     = "dmplt-uc-credential"
  azure_managed_identity {
    access_connector_id = var.access_connector_id
  }
  depends_on = [databricks_metastore_assignment.this]
}

# --- One external location + catalog per environment ---
resource "databricks_external_location" "this" {
  provider        = databricks.workspace
  for_each        = var.container_names
  name            = "dmplt-loc-${each.key}"
  url             = "abfss://${each.value}@${var.storage_account_name}.dfs.core.windows.net/"
  credential_name = databricks_storage_credential.this.name
}

resource "databricks_catalog" "this" {
  provider     = databricks.workspace
  for_each     = var.container_names
  name         = upper(each.key) # DEV / PRE / PRO
  storage_root = databricks_external_location.this[each.key].url
  owner        = var.catalog_owner
  comment      = "Managed by Terraform — ${upper(each.key)} environment"
}

# devops automation privileges on each catalog.
resource "databricks_grants" "devops" {
  provider = databricks.workspace
  for_each = databricks_catalog.this
  catalog  = each.value.name
  grant {
    principal  = var.devops_principal
    privileges = ["USE_CATALOG", "USE_SCHEMA", "CREATE_SCHEMA"]
  }
}
```

- [ ] **Step 3: Create module outputs**

Create `infra/terraform/modules/unity_catalog/outputs.tf`:

```hcl
output "catalog_names" {
  value = { for k, c in databricks_catalog.this : k => c.name }
}
output "metastore_id" { value = databricks_metastore.this.id }
```

- [ ] **Step 4: Wire module**

In `infra/terraform/main.tf` append:

```hcl
module "unity_catalog" {
  source               = "./modules/unity_catalog"
  location             = var.location
  workspace_id         = module.databricks_workspace.workspace_id
  access_connector_id  = module.databricks_workspace.access_connector_id
  storage_account_name = module.storage.storage_account_name
  container_names      = module.storage.container_names
  catalog_owner        = module.identities.admin_client_id
  devops_principal     = module.identities.devops_client_id

  providers = {
    databricks.account   = databricks.account
    databricks.workspace = databricks.workspace
  }
}
```

Add to `infra/terraform/outputs.tf`:

```hcl
output "catalog_names" { value = module.unity_catalog.catalog_names }
output "databricks_workspace_url" { value = module.databricks_workspace.workspace_url }
```

Also add the `databricks` provider requirement to the module by creating `infra/terraform/modules/unity_catalog/versions.tf`:

```hcl
terraform {
  required_providers {
    databricks = {
      source                = "databricks/databricks"
      configuration_aliases = [databricks.account, databricks.workspace]
    }
  }
}
```

- [ ] **Step 5: Validate**

Run:
```bash
cd infra/terraform && terraform init -backend=false && terraform validate && terraform fmt -check -recursive
```
Expected: `Success! The configuration is valid.`

- [ ] **Step 6: Commit**

```bash
git add infra/terraform/modules/unity_catalog/ infra/terraform/main.tf infra/terraform/outputs.tf
git commit -m "feat(infra): unity_catalog module (metastore, credential, DEV/PRE/PRO catalogs)"
```

---

### Task 10: Import script + runbook README

**Files:**
- Create: `infra/terraform/import.sh`
- Create: `infra/terraform/README.md`

**Interfaces:**
- Consumes: all existing Azure resource IDs.
- Produces: documented `terraform import` workflow and end-to-end runbook.

- [ ] **Step 1: Create import.sh**

Create `infra/terraform/import.sh`:

```bash
#!/bin/bash
set -euo pipefail

# Imports existing Azure resources into Terraform state so they are NOT recreated.
# Prereqs: `terraform init` (remote backend) completed; SUBSCRIPTION_ID exported.
: "${SUBSCRIPTION_ID:?Must export SUBSCRIPTION_ID}"

RG="dmplt-rg"
BASE="/subscriptions/${SUBSCRIPTION_ID}/resourceGroups/${RG}"

terraform import 'module.core.azurerm_resource_group.main' "${BASE}"
terraform import 'module.core.azurerm_container_registry.main' "${BASE}/providers/Microsoft.ContainerRegistry/registries/dmpltacr"
terraform import 'module.core.azurerm_container_app_environment.main' "${BASE}/providers/Microsoft.App/managedEnvironments/dmplt-cae"
terraform import 'module.backend_app.azurerm_container_app.backend' "${BASE}/providers/Microsoft.App/containerApps/dmplt-ca-backend"
terraform import 'module.frontend.azurerm_static_web_app.frontend' "${BASE}/providers/Microsoft.Web/staticSites/dmplt-stapp-frontend"

echo ""
echo "If a Log Analytics workspace already backs dmplt-cae, import it too, e.g.:"
echo "  terraform import 'module.core.azurerm_log_analytics_workspace.main' <law-resource-id>"
echo ""
echo "Now run: terraform plan   (MUST show no destroy/replace on imported resources)"
```

- [ ] **Step 2: Create README runbook**

Create `infra/terraform/README.md`:

```markdown
# Data Mesh Platform — Terraform Infrastructure

All Azure infrastructure is managed here. Region: `westus2`.

## One-time bootstrap

1. **State backend** (creates `dmplttfstate` storage):
   ```bash
   cd bootstrap && terraform init && terraform apply -var="subscription_id=<SUB_ID>" && cd ..
   ```
2. **Databricks account admin**: in the Databricks Account Console
   (https://accounts.azuredatabricks.net), add the `dmplt-admin` service
   principal (its `client_id`, output by Task 3 apply) as an **account admin**.
   Required so Terraform can create the Unity Catalog metastore.
   (Chicken-and-egg: SP is created by `terraform apply`; grant admin after the
   identities module applies, before applying the unity_catalog module — see
   "Phased apply" below.)
3. Get the **Databricks Account ID** from the Account Console → set
   `databricks_account_id` in `terraform.tfvars`.

## Configure

```bash
cp terraform.tfvars.example terraform.tfvars   # fill in real values (gitignored)
terraform init    # uses remote azurerm backend
```

## Import existing resources (first run only)

```bash
export SUBSCRIPTION_ID=<SUB_ID>
bash import.sh
terraform plan    # MUST show zero destroy/replace on imported resources
```

## Phased apply (handles the UC account-admin bootstrap)

```bash
# 1) Create identities first, then grant dmplt-admin account admin in the Console.
terraform apply -target=module.identities
#    -> grant account admin to dmplt-admin (step 2 above), then:
# 2) Apply everything else.
terraform apply
```

Steady state (after bootstrap): `terraform plan` / `terraform apply`.

## Costs

Only fixed cost is ACR Basic (~$5/mo). Databricks Premium has no idle cost
(DBU pay-per-use); no clusters/SQL warehouses are provisioned here. Storage is
Standard LRS; Container App scales to zero; Static Web App is Free.

## Outputs

- `admin_client_id` / `admin_client_secret` (sensitive)
- `devops_client_id` / `devops_client_secret` (sensitive)
- `databricks_workspace_url`, `catalog_names`

Retrieve sensitive outputs: `terraform output -raw admin_client_secret`.
```

- [ ] **Step 3: Validate**

Run:
```bash
bash -n infra/terraform/import.sh && echo "import.sh syntax OK"
```
Expected: `import.sh syntax OK`

- [ ] **Step 4: Commit**

```bash
git add infra/terraform/import.sh infra/terraform/README.md
git commit -m "docs(infra): import script and terraform runbook"
```

---

### Task 11: GitHub Actions `infra.yml` (plan on PR, apply via OIDC)

**Files:**
- Create: `.github/workflows/infra.yml`

**Interfaces:**
- Consumes: GitHub secrets `AZURE_CLIENT_ID` (dmplt-devops client id), `AZURE_TENANT_ID`, `AZURE_SUBSCRIPTION_ID`, `DATABRICKS_ACCOUNT_ID`, `ARM_CLIENT_ID`/`ARM_*` as needed.
- Produces: CI that validates+plans on PR and applies on dispatch/main.

- [ ] **Step 1: Create workflow**

Create `.github/workflows/infra.yml`:

```yaml
name: Infra (Terraform)

on:
  pull_request:
    paths:
      - 'infra/terraform/**'
      - '.github/workflows/infra.yml'
  push:
    branches: [main]
    paths:
      - 'infra/terraform/**'
  workflow_dispatch:

permissions:
  id-token: write   # OIDC
  contents: read
  pull-requests: write

env:
  TF_VERSION: "1.9.5"
  WORKDIR: infra/terraform
  ARM_USE_OIDC: "true"
  ARM_CLIENT_ID: ${{ secrets.AZURE_CLIENT_ID }}
  ARM_TENANT_ID: ${{ secrets.AZURE_TENANT_ID }}
  ARM_SUBSCRIPTION_ID: ${{ secrets.AZURE_SUBSCRIPTION_ID }}
  TF_VAR_subscription_id: ${{ secrets.AZURE_SUBSCRIPTION_ID }}
  TF_VAR_tenant_id: ${{ secrets.AZURE_TENANT_ID }}
  TF_VAR_databricks_account_id: ${{ secrets.DATABRICKS_ACCOUNT_ID }}

jobs:
  plan:
    name: Validate & Plan
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: azure/login@v2
        with:
          client-id: ${{ secrets.AZURE_CLIENT_ID }}
          tenant-id: ${{ secrets.AZURE_TENANT_ID }}
          subscription-id: ${{ secrets.AZURE_SUBSCRIPTION_ID }}

      - uses: hashicorp/setup-terraform@v3
        with:
          terraform_version: ${{ env.TF_VERSION }}

      - name: Format check
        working-directory: ${{ env.WORKDIR }}
        run: terraform fmt -check -recursive

      - name: Init
        working-directory: ${{ env.WORKDIR }}
        run: terraform init

      - name: Validate
        working-directory: ${{ env.WORKDIR }}
        run: terraform validate

      - name: Plan
        working-directory: ${{ env.WORKDIR }}
        run: terraform plan -input=false -no-color

  apply:
    name: Apply
    runs-on: ubuntu-latest
    needs: plan
    if: github.event_name == 'push' || github.event_name == 'workflow_dispatch'
    concurrency:
      group: infra-apply
      cancel-in-progress: false
    steps:
      - uses: actions/checkout@v4

      - uses: azure/login@v2
        with:
          client-id: ${{ secrets.AZURE_CLIENT_ID }}
          tenant-id: ${{ secrets.AZURE_TENANT_ID }}
          subscription-id: ${{ secrets.AZURE_SUBSCRIPTION_ID }}

      - uses: hashicorp/setup-terraform@v3
        with:
          terraform_version: ${{ env.TF_VERSION }}

      - name: Init
        working-directory: ${{ env.WORKDIR }}
        run: terraform init

      - name: Apply
        working-directory: ${{ env.WORKDIR }}
        run: terraform apply -input=false -auto-approve
```

- [ ] **Step 2: Validate workflow YAML**

Run:
```bash
python -c "import yaml,sys; yaml.safe_load(open('.github/workflows/infra.yml')); print('infra.yml YAML OK')"
```
Expected: `infra.yml YAML OK`

- [ ] **Step 3: Commit**

```bash
git add .github/workflows/infra.yml
git commit -m "ci(infra): terraform plan/apply workflow via OIDC"
```

---

### Task 12: Retire azure-setup.sh and document the new flow

**Files:**
- Delete: `scripts/azure-setup.sh`
- Modify: `docs/superpowers/specs/2026-04-05-azure-cd-design.md:152-157` (note IaC migration)
- Modify: `README.md` (deploy section pointer, if present)

**Interfaces:**
- Consumes: nothing.
- Produces: single source of truth = Terraform; no stale manual script.

- [ ] **Step 1: Confirm import is verified before deletion**

This task's deletion is only valid AFTER Task 10's `terraform plan` (run during execution against live Azure) confirms the imported resources match. If import has not yet been verified in your environment, keep `scripts/azure-setup.sh` until it has. Proceed only when verified.

- [ ] **Step 2: Delete the manual setup script**

```bash
git rm scripts/azure-setup.sh
```

- [ ] **Step 3: Add migration note to the old spec**

In `docs/superpowers/specs/2026-04-05-azure-cd-design.md`, replace the `## Out of Scope` line `- No Bicep / IaC — infrastructure created manually via setup script` with:

```markdown
- ~~No Bicep / IaC — infrastructure created manually via setup script~~ **Superseded 2026-06-22:** all infrastructure is now Terraform-managed under `infra/terraform/` (see `docs/superpowers/specs/2026-06-22-terraform-azure-databricks-design.md`). `scripts/azure-setup.sh` was removed.
```

- [ ] **Step 4: Validate references**

Run:
```bash
grep -rn "azure-setup.sh" --include="*.md" --include="*.yml" . || echo "no stale references"
```
Expected: `no stale references` (or only the historical mention you just edited).

- [ ] **Step 5: Commit**

```bash
git add -A
git commit -m "chore(infra): retire azure-setup.sh in favor of Terraform"
```

---

## Self-Review

**1. Spec coverage:**
- Migrate all Azure deploy to Terraform → Tasks 2–10 (modules + import + runbook). ✅
- Import existing resources → Task 10 `import.sh` + phased plan gate. ✅
- Remote state → Task 1 (bootstrap) + Task 2 (`backend.tf`). ✅
- GitHub Actions apply via OIDC → Task 11 + Task 3 federated credentials. ✅
- SPNs `dmplt-admin` & `dmplt-devops` via Terraform → Task 3. ✅
- SPN roles (admin=governance/catalog owner, devops=CI/CD + grants) → Task 3 (Contributor + OIDC), Task 9 (catalog owner + grants). ✅
- Databricks `dmplt-adb` Premium, no VNet → Task 8. ✅
- Storage `dmpltsta` ADLS Gen2 + 3 containers → Task 7. ✅
- 3 catalogs DEV/PRE/PRO via UC, 1 storage / 3 containers → Task 9. ✅
- Metastore created via TF, no root storage, westus2 → Task 9. ✅
- Lowest-cost choices → Global Constraints + Tasks 4/6/7/8. ✅
- Image rollout stays in cd.yml (ignore drift) → Task 5 lifecycle. ✅
- Retire manual script → Task 12. ✅

**2. Placeholder scan:** No TBD/TODO/"handle appropriately" — every step has concrete HCL/commands. ✅

**3. Type consistency:** Cross-module output names verified — `module.core.*`, `module.storage.storage_account_name`/`container_names`, `module.databricks_workspace.workspace_id`/`workspace_url`/`access_connector_id`/`access_connector_principal_id`, `module.identities.admin_client_id`/`devops_client_id` are consistently produced and consumed. `container_names` is a `map(string)` keyed dev/pre/pro, consumed by `for_each` in Task 9. ✅

**Note for executor:** `terraform validate -backend=false` exercises syntax/schema only. The correctness of imports and UC account-admin bootstrap can only be confirmed by `terraform plan`/`apply` against live Azure with valid credentials and the Databricks account_id — perform those during execution (runbook in Task 10), not as part of the per-task validate gate.

---

## Execution

Plan complete and saved to `docs/superpowers/plans/2026-06-22-terraform-azure-databricks.md`.
```
