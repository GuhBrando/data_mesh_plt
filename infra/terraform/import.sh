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
echo "IMPORTANT — Log Analytics workspace:"
echo "  If a Log Analytics workspace already backs dmplt-cae (check Azure portal),"
echo "  it MUST be imported as 'module.core.azurerm_log_analytics_workspace.main'"
echo "  BEFORE running 'terraform apply', or Terraform will create a duplicate dmplt-law."
echo "  Import command:"
echo "    terraform import 'module.core.azurerm_log_analytics_workspace.main' <law-resource-id>"
echo ""
echo "NOTE: dmpltsta (storage account) and its containers are NEW resources — do NOT import them."
echo ""
echo "Now run: terraform plan   (MUST show no destroy/replace on imported resources)"
