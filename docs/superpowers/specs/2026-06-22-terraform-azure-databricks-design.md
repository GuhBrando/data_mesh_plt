# Terraform Azure Deploy + Databricks (Unity Catalog) — Design Spec

**Date:** 2026-06-22
**Author:** GuhBrando
**Status:** Approved

---

## Overview

Migrate **all** Azure infrastructure provisioning from the manual `scripts/azure-setup.sh` + ad-hoc `az` commands to **Terraform**, and extend the platform with a **Databricks** workspace governed by **Unity Catalog**.

New capabilities:
- Databricks workspace `dmplt-adb` (Premium SKU — required for Unity Catalog).
- ADLS Gen2 storage account `dmpltsta` (data generated in Databricks).
- 3 Unity Catalog catalogs: `DEV`, `PRE`, `PRO`.
- 2 Service Principals (Azure AD apps): `dmplt-admin` (governance) and `dmplt-devops` (CI/CD automation).

**Determining constraint:** lowest cost always, balanced so no functionality is lost (see Cost Model).

---

## Decisions (from brainstorming)

| Topic | Decision |
|---|---|
| Existing Azure resources | **Import** into Terraform (no recreate, no data loss) |
| Terraform state backend | **Remote** `azurerm` backend in a dedicated Storage Account |
| Terraform execution | **GitHub Actions** (plan on PR, apply on dispatch/main) via **OIDC** on `dmplt-devops` |
| SPN creation | Created **by Terraform** (`azuread` provider) |
| SPN roles | `dmplt-admin` = governance (Databricks account admin + metastore admin + catalog owner); `dmplt-devops` = automation (Terraform runner / CI / data access) |
| Storage layout | **1 storage account, 3 containers** (`dev`/`pre`/`pro`), each mapped to a catalog via external location |
| UC metastore | **Create via Terraform**, no existing metastore in region |
| Region | **westus2** (same as current environment) |
| Image rollout | Container App owned by TF but with `ignore_changes` on image; `cd.yml` keeps doing `az containerapp update` per release tag |
| CI auth | **OIDC federated credentials** on `dmplt-devops` (no long-lived secrets in GitHub) |

---

## Architecture

```
                 ┌─────────────────────── Terraform (infra/terraform/) ───────────────────────┐
                 │                                                                              │
 azuread  ───────┼─► dmplt-admin SP (governance)   dmplt-devops SP (CI/CD, OIDC federated)     │
                 │                                                                              │
 azurerm  ───────┼─► [IMPORT] dmplt-rg, dmpltacr(Basic), dmplt-cae, dmplt-ca-backend,          │
                 │            dmplt-stapp-frontend                                              │
                 │   [NEW]    dmplt-adb (Databricks Premium, no-VNet), Access Connector (MI),   │
                 │            dmpltsta (ADLS Gen2, Standard LRS, HNS) + containers dev/pre/pro   │
                 │                                                                              │
 databricks ─────┼─► (account) metastore + metastore_assignment(dmplt-adb)                     │
   (account)     │   (workspace) storage_credential → 3 external_location → DEV/PRE/PRO catalogs│
   (workspace)   │            + grants (owner=dmplt-admin, usage=dmplt-devops)                  │
                 └──────────────────────────────────────────────────────────────────────────────┘

 cd.yml (unchanged role): build/push image to ACR → az containerapp update → Static Web App deploy
 infra.yml (new): fmt/validate/tflint + plan on PR; apply on workflow_dispatch / push to main
```

---

## File Structure

```
infra/terraform/
  bootstrap/
    main.tf                  # RG dmplt-tfstate-rg + Storage dmplttfstate + container tfstate (run once, local state)
    README.md
  backend.tf                 # backend "azurerm" → dmplttfstate / tfstate / data_mesh_plt.tfstate
  providers.tf               # azurerm, azuread, databricks (account alias + workspace alias)
  versions.tf                # required_providers + version pins
  variables.tf
  outputs.tf
  terraform.tfvars.example
  main.tf                    # module wiring
  import.sh                  # terraform import commands for existing resources
  README.md                  # bootstrap + import + apply runbook
  modules/
    identities/              # azuread apps + SPs (dmplt-admin, dmplt-devops), client secrets, OIDC federated creds, Azure role assignments
    core/                    # RG, ACR (Basic), Log Analytics (30d), Container Apps Env   [IMPORT]
    backend_app/             # Container App dmplt-ca-backend (secrets/env, ignore_changes=image)  [IMPORT]
    frontend/                # Static Web App dmplt-stapp-frontend (Free)   [IMPORT]
    databricks_workspace/    # azurerm_databricks_workspace dmplt-adb (Premium, no VNet injection) + Access Connector
    storage/                 # azurerm_storage_account dmpltsta (Standard LRS, HNS) + 3 containers + role assignment to Access Connector
    unity_catalog/           # metastore, metastore_assignment, storage_credential, 3 external_location, 3 catalogs, grants

.github/workflows/
  infra.yml                  # NEW — Terraform CI/CD (OIDC via dmplt-devops)
  cd.yml                     # KEPT — app build/deploy (image rollout) + frontend
```

`scripts/azure-setup.sh` is **retired** (removed) once import is verified; its provisioning role is replaced by Terraform. The runbook in `infra/terraform/README.md` documents the new process.

---

## Providers

```hcl
required_providers {
  azurerm    = { source = "hashicorp/azurerm",    version = "~> 4.0" }
  azuread    = { source = "hashicorp/azuread",     version = "~> 3.0" }
  databricks = { source = "databricks/databricks", version = "~> 1.50" }
}
```

- `azurerm` — all Azure resources.
- `azuread` — App Registrations + Service Principals + OIDC federated credentials.
- `databricks` configured twice via aliases:
  - `databricks.account` — `host = https://accounts.azuredatabricks.net`, `account_id = var.databricks_account_id`. Authenticated as `dmplt-admin`. Used for **metastore** and **metastore_assignment**.
  - `databricks.workspace` — `host = azurerm_databricks_workspace.dmplt_adb.workspace_url`. Used for **storage_credential, external_location, catalogs, grants**.

---

## Unity Catalog Data Flow

```
dmpltsta (ADLS Gen2, HNS)
  ├── container: dev  ──► external_location dev  ──► catalog DEV
  ├── container: pre  ──► external_location pre  ──► catalog PRE
  └── container: pro  ──► external_location pro  ──► catalog PRO

Access Connector (system-assigned managed identity)
  └── role: Storage Blob Data Contributor on dmpltsta
      └── databricks_storage_credential (Azure managed identity = Access Connector)
          └── used by all 3 external_locations
```

- Metastore created **without root storage** (modern model — managed storage defined per catalog/external location). Avoids an extra storage account.
- Catalog owner = `dmplt-admin`. `dmplt-devops` granted `USE_CATALOG` / `USE_SCHEMA` / `CREATE` for automation.

---

## Cost Model (lowest-cost choices)

| Resource | Choice | Cost |
|---|---|---|
| Databricks `dmplt-adb` | Premium SKU (required for UC), **no VNet injection** (no NAT Gateway) | $0 idle — DBU pay-per-use only |
| Databricks compute | **None provisioned by TF** (clusters/SQL warehouses out of scope) | $0 until user starts compute |
| UC metastore | No root storage | $0 |
| Storage `dmpltsta` | Standard, **LRS**, HNS; optional Cool lifecycle | pennies until data lands |
| ACR `dmpltacr` | **Basic** (cheapest with private push) | ~$5/month (only fixed cost) |
| Container App backend | **min-replicas 0** (scale-to-zero) | pay-per-request |
| Container Apps Env / Log Analytics | reuse existing; retention **30 days** | minimal |
| Static Web App | **Free tier** | $0 |
| Access Connector / SPNs | managed identity + AAD apps | $0 |
| tfstate storage | Standard LRS, tiny | cents |

**Only fixed cost:** ACR Basic (~$5/month). Everything else is consumption / scale-to-zero / free tier.

---

## Bootstrap & Prerequisites (runbook)

Documented in `infra/terraform/README.md`:

1. **State backend bootstrap (once):** `cd infra/terraform/bootstrap && terraform init && terraform apply` → creates `dmplt-tfstate-rg`, storage `dmplttfstate`, container `tfstate` (local state for this small step).
2. **Databricks account_id:** supply as `var.databricks_account_id` (from Databricks Account Console).
3. **Account-admin bootstrap (chicken-and-egg of UC):** add the `dmplt-admin` Service Principal as a **Databricks account admin** in the Account Console once, so Terraform can create the metastore. Documented step.
4. **Import existing resources:** `terraform init` (remote backend) → run `import.sh` (imports `dmplt-rg`, `dmpltacr`, `dmplt-cae`, `dmplt-ca-backend`, `dmplt-stapp-frontend`). Verify `terraform plan` shows **no destructive changes**.
5. **Apply:** `terraform apply` provisions the new Databricks/storage/UC/identities stack.

---

## CI/CD Integration

### `infra.yml` (new)
- **On PR touching `infra/terraform/**`:** `terraform fmt -check`, `terraform validate`, `tflint`, `terraform plan` (comment plan output).
- **On `workflow_dispatch` / push to `main`:** `terraform apply`.
- **Auth:** OIDC federated credential on `dmplt-devops` SP (`azure/login@v2` with `client-id`/`tenant-id`/`subscription-id`, no client secret). Databricks provider authenticates via the same Azure identity / `dmplt-admin` secret stored as GitHub secret for account-level ops.

### `cd.yml` (kept, role unchanged)
- Build & push backend image to ACR; `az containerapp update` rolls out the new tag (TF ignores image drift); deploy frontend to Static Web Apps.

---

## Testing & Validation

- `terraform fmt -check` + `terraform validate` + `tflint` in CI (and locally pre-commit).
- `terraform plan` after import must show **zero destroy/replace** on imported resources — the import correctness gate.
- Post-apply smoke: confirm `dmplt-adb` reachable, metastore assigned, 3 catalogs visible, each external location validates (Databricks `external_location` validation), and `dmpltsta` containers exist.

---

## Edge Cases

- **Storage name uniqueness:** `dmpltsta` (8 chars) and `dmplttfstate` (12 chars) are valid (3–24 lowercase alphanumeric) and assumed globally available; fallback suffix documented if taken.
- **Metastore per region:** only one metastore per region (westus2); apply fails clearly if one already exists → reuse path documented.
- **Image drift:** `lifecycle { ignore_changes = [template[0].container[0].image] }` on the Container App.
- **Secret handling:** SP client secrets and `databricks_account_id` are sensitive vars / TF outputs marked `sensitive`; surfaced for GitHub secrets, never committed.

---

## Out of Scope

- PostgreSQL migration (stays on Neon / external).
- Databricks notebooks, jobs, DLT pipelines, clusters, SQL warehouses (data workloads).
- Multi-environment via TF workspaces (the 3 UC catalogs provide the DEV/PRE/PRO separation).
- Rollback automation.
