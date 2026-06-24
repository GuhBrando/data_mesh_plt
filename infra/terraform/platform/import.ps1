# Imports pre-existing Azure resources into the PLATFORM stack state so they are
# NOT recreated. Run ONCE, after `terraform init`, from this directory.
#
#   $env:SUBSCRIPTION_ID = "<sub-id>"
#   ./import.ps1
#
# Unlike the old monolith, the platform stack has only azurerm/azuread providers,
# so import works WITHOUT any temporary neutralization.
#
# NOTE: dmpltsta (storage), the Databricks workspace, the access connector and the
# role assignment are NEW resources created by `terraform apply` — do NOT import them.

$ErrorActionPreference = "Stop"
if (-not $env:SUBSCRIPTION_ID) { throw "Set `$env:SUBSCRIPTION_ID first." }
$base = "/subscriptions/$($env:SUBSCRIPTION_ID)/resourceGroups/dmplt-rg"

terraform import 'module.core.azurerm_resource_group.main' "$base"
terraform import 'module.core.azurerm_container_registry.main' "$base/providers/Microsoft.ContainerRegistry/registries/dmpltacr"
terraform import 'module.core.azurerm_container_app_environment.main' "$base/providers/Microsoft.App/managedEnvironments/dmplt-cae"
terraform import 'module.backend_app.azurerm_container_app.backend' "$base/providers/Microsoft.App/containerApps/dmplt-ca-backend"
terraform import 'module.frontend.azurerm_static_web_app.frontend' "$base/providers/Microsoft.Web/staticSites/dmplt-stapp-frontend"

Write-Host ""
Write-Host "IMPORTANT - Log Analytics workspace:" -ForegroundColor Yellow
Write-Host "  If a Log Analytics workspace already backs dmplt-cae, import it as"
Write-Host "  'module.core.azurerm_log_analytics_workspace.main' BEFORE 'terraform apply',"
Write-Host "  or Terraform will create a duplicate dmplt-law."
Write-Host ""
Write-Host "Now run: terraform plan   (MUST show no destroy/replace on imported resources)"
