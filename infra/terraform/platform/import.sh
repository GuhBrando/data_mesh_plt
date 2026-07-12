#!/bin/bash
set -euo pipefail

# Imports pre-existing Azure resources into the PLATFORM stack state so they are
# NOT recreated. Run ONCE, after `terraform init`, from this directory.
#
#   export SUBSCRIPTION_ID=<sub-id>
#   bash import.sh
#
# Unlike the old monolith, the platform stack has only azurerm/azuread providers,
# so import works WITHOUT any temporary neutralization.
#
# NOTE: dmpltsta (storage), the Databricks workspace, the access connector and the
# role assignment are NEW resources created by `terraform apply` — do NOT import them.

: "${SUBSCRIPTION_ID:?Must export SUBSCRIPTION_ID}"
BASE="/subscriptions/${SUBSCRIPTION_ID}/resourceGroups/dmplt-rg"

terraform import 'module.core.azurerm_resource_group.main' "${BASE}"
terraform import 'module.core.azurerm_container_registry.main' "${BASE}/providers/Microsoft.ContainerRegistry/registries/dmpltacr"
terraform import 'module.core.azurerm_container_app_environment.main' "${BASE}/providers/Microsoft.App/managedEnvironments/dmplt-cae"
terraform import 'module.backend_app.azurerm_container_app.backend' "${BASE}/providers/Microsoft.App/containerApps/dmplt-ca-backend"
terraform import 'module.frontend.azurerm_static_web_app.frontend' "${BASE}/providers/Microsoft.Web/staticSites/dmplt-stapp-frontend"

echo ""
echo "IMPORTANT — Log Analytics workspace:"
echo "  If a Log Analytics workspace already backs dmplt-cae, import it as"
echo "  'module.core.azurerm_log_analytics_workspace.main' BEFORE 'terraform apply',"
echo "  or Terraform will create a duplicate dmplt-law."
echo ""
echo "Now run: terraform plan   (MUST show no destroy/replace on imported resources)"
