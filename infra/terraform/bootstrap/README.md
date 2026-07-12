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
