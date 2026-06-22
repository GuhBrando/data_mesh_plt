#!/bin/bash
set -e

# ============================================================================
# DEPRECATED (2026-06-22): Infrastructure is now managed by Terraform under
# infra/terraform/ (see infra/terraform/README.md). This script is retained
# only as a manual fallback until `terraform import` is verified against live
# Azure (terraform plan showing zero destroy/replace). Remove it after that.
# ============================================================================

# Prerequisites:
#   1. Azure CLI installed and logged in (az login)
#   2. Export these variables before running:
#
#   export POSTGRES_PASSWORD="<neon password>"   # from Neon dashboard
#   export NEON_HOST="<neon pooler host>"         # e.g. ep-xxx-pooler.us-west-2.aws.neon.tech
#   export NEON_DIRECT_HOST="<neon direct host>"  # e.g. ep-xxx.us-west-2.aws.neon.tech (no -pooler)
#   export ADMIN_PASSWORD="<strong password>"
#   export APP_USER_PASSWORD="<strong password>"
#   export USER_PASSWORD="<strong password>"

: "${POSTGRES_PASSWORD:?Must export POSTGRES_PASSWORD}"
: "${NEON_HOST:?Must export NEON_HOST}"
: "${NEON_DIRECT_HOST:?Must export NEON_DIRECT_HOST}"
: "${ADMIN_PASSWORD:?Must export ADMIN_PASSWORD}"
: "${APP_USER_PASSWORD:?Must export APP_USER_PASSWORD}"
: "${USER_PASSWORD:?Must export USER_PASSWORD}"

RESOURCE_GROUP="dmplt-rg"
LOCATION="westus2"
ACR_NAME="dmpltacr"
CAE_NAME="dmplt-cae"
BACKEND_APP="dmplt-ca-backend"
STATIC_APP="dmplt-stapp-frontend"
SUBSCRIPTION_ID=$(az account show --query id -o tsv)

echo "=== [0/7] Registering required resource providers ==="
az provider register --namespace Microsoft.Web --wait
az provider register --namespace Microsoft.App --wait
az provider register --namespace Microsoft.ContainerRegistry --wait

echo "=== [1/7] Creating Resource Group ==="
az group create --name "$RESOURCE_GROUP" --location "$LOCATION"

echo "=== [2/7] Creating Container Registry ==="
az acr create \
  --name "$ACR_NAME" \
  --resource-group "$RESOURCE_GROUP" \
  --sku Basic \
  --admin-enabled true

echo "=== [3/7] Creating Container Apps Environment ==="
az containerapp env create \
  --name "$CAE_NAME" \
  --resource-group "$RESOURCE_GROUP" \
  --location "$LOCATION"

echo "=== [4/6] Creating Backend Container App ==="
ACR_USERNAME=$(az acr credential show -n "$ACR_NAME" --query username -o tsv)
ACR_PASSWORD=$(az acr credential show -n "$ACR_NAME" --query "passwords[0].value" -o tsv)

az containerapp create \
  --name "$BACKEND_APP" \
  --resource-group "$RESOURCE_GROUP" \
  --environment "$CAE_NAME" \
  --image mcr.microsoft.com/azuredocs/containerapps-helloworld:latest \
  --ingress external \
  --target-port 8000 \
  --min-replicas 0 \
  --max-replicas 2 \
  --registry-server "$ACR_NAME.azurecr.io" \
  --registry-username "$ACR_USERNAME" \
  --registry-password "$ACR_PASSWORD" \
  --env-vars \
    DB_HOST="$NEON_HOST" \
    MIGRATIONS_DB_HOST="$NEON_DIRECT_HOST" \
    DB_PORT=5432 \
    DB_NAME=data_mesh_plt \
    DB_USER=admin \
    "POSTGRES_PASSWORD=secretref:postgres-password" \
    "ADMIN_PASSWORD=secretref:admin-password" \
    "APP_USER_PASSWORD=secretref:app-user-password" \
    "USER_PASSWORD=secretref:user-password" \
  --secrets \
    "postgres-password=$POSTGRES_PASSWORD" \
    "admin-password=$ADMIN_PASSWORD" \
    "app-user-password=$APP_USER_PASSWORD" \
    "user-password=$USER_PASSWORD"

echo "=== [5/6] Creating Static Web App ==="
az staticwebapp create \
  --name "$STATIC_APP" \
  --resource-group "$RESOURCE_GROUP" \
  --location "$LOCATION"

echo "=== [6/6] Creating Service Principal for GitHub Actions ==="
az ad sp create-for-rbac \
  --name "sp-dmplt-github-actions" \
  --role contributor \
  --scopes "/subscriptions/$SUBSCRIPTION_ID/resourceGroups/$RESOURCE_GROUP" \
  --json-auth

echo ""
echo "============================================================"
echo "  GitHub Secrets — copy each value to your repository"
echo "  Settings > Secrets and variables > Actions > New secret"
echo "============================================================"
echo ""
echo "Secret: AZURE_CREDENTIALS"
echo "  Value: (the JSON block printed above by az ad sp create-for-rbac)"
echo ""
echo "Secret: ACR_USERNAME"
az acr credential show -n "$ACR_NAME" --query username -o tsv
echo ""
echo "Secret: ACR_PASSWORD"
az acr credential show -n "$ACR_NAME" --query "passwords[0].value" -o tsv
echo ""
echo "Secret: AZURE_STATIC_WEB_APPS_API_TOKEN"
az staticwebapp secrets list -n "$STATIC_APP" --query properties.apiKey -o tsv
echo ""
echo "Secret: VITE_API_URL (backend public URL):"
BACKEND_FQDN=$(az containerapp show \
  -n "$BACKEND_APP" -g "$RESOURCE_GROUP" \
  --query properties.configuration.ingress.fqdn -o tsv)
echo "https://$BACKEND_FQDN"
echo ""
echo "Secret: DB_HOST"
echo "  Value: $NEON_HOST  (from Neon dashboard)"
echo ""
echo "Secret: POSTGRES_PASSWORD"
echo "  Value: your Neon password  (from Neon dashboard)"
echo ""
echo "Secrets: ADMIN_PASSWORD, APP_USER_PASSWORD, USER_PASSWORD"
echo "  Values: the same passwords you exported before running this script"
echo ""
echo "Secret: CORS_ORIGINS"
echo "  Value: comma-separated list of allowed frontend origins (e.g. https://your-frontend.azurestaticapps.net)"
echo "============================================================"
