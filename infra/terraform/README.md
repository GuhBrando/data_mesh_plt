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

### Name verification

Before importing, confirm the live resource names match this config (`dmplt-rg`,
`dmpltacr`, `dmplt-cae`, `dmplt-ca-backend`, `dmplt-stapp-frontend`). These names
match `scripts/azure-setup.sh`; any mismatch means Terraform will create a new
resource and potentially replace the existing one.

### Log Analytics note

The existing `dmplt-cae` was created without an explicit Log Analytics workspace,
so Azure may have auto-generated one with a different name. This config declares an
explicit `dmplt-law`. Before the first apply, either:
- (a) Import the existing auto-generated LAW as
  `module.core.azurerm_log_analytics_workspace.main`, or
- (b) Accept that `terraform plan` will want to create `dmplt-law` and re-point
  the CAE — verify `terraform plan` shows **NO destroy/replace on `dmplt-cae`**.

Resolve this during import verification.

### New resources (not imported)

The storage account `dmpltsta` and its containers are **new** resources — they are
created by Terraform and intentionally NOT imported.

## Phased apply (handles the UC account-admin bootstrap)

The `databricks.workspace` provider is configured from the workspace module's
outputs, so the workspace must exist before any Unity Catalog resource is planned.
Run applies in this order:

```bash
# 1) Identities first; then grant dmplt-admin account admin in the Databricks Account Console.
terraform apply -target=module.identities
# 2) Create the Databricks workspace + access connector + storage role assignment
#    (the databricks.workspace provider is configured from these outputs).
terraform apply -target=module.databricks_workspace -target=azurerm_role_assignment.uc_storage
# 3) Full apply (metastore, catalogs, grants, and the rest).
terraform apply
```

Steady state (after bootstrap): `terraform plan` / `terraform apply`.

### Permissions note

Creating Azure role assignments (`azurerm_role_assignment.uc_storage` and the
devops Contributor assignment) requires `Owner` or `User Access Administrator` —
plain `Contributor` cannot create role assignments. Either run the
role-assignment-creating applies (steps 1 and 2) with a privileged human identity,
or grant the CI principal `User Access Administrator`.

The devops Contributor assignment is subscription-scoped for bootstrap convenience
and SHOULD be tightened to the relevant resource group(s) for least privilege once
the infrastructure is stable.

## Costs

Only fixed cost is ACR Basic (~$5/mo). Databricks Premium has no idle cost
(DBU pay-per-use); no clusters/SQL warehouses are provisioned here. Storage is
Standard LRS; Container App scales to zero; Static Web App is Free.

## Outputs

- `admin_client_id` / `admin_client_secret` (sensitive)
- `devops_client_id` (devops authenticates via OIDC — no client secret output)
- `databricks_workspace_url`, `catalog_names`

Retrieve sensitive outputs: `terraform output -raw admin_client_secret`.
