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
