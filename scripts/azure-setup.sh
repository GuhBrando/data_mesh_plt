#!/bin/bash
set -e

# Prerequisites:
#   1. Azure CLI installed and logged in (az login)
#   2. Export these variables before running:
#
#   export POSTGRES_PASSWORD="<strong password>"
#   export ADMIN_PASSWORD="<strong password>"
#   export APP_USER_PASSWORD="<strong password>"
#   export USER_PASSWORD="<strong password>"

: "${POSTGRES_PASSWORD:?Must export POSTGRES_PASSWORD}"
: "${ADMIN_PASSWORD:?Must export ADMIN_PASSWORD}"
: "${APP_USER_PASSWORD:?Must export APP_USER_PASSWORD}"
: "${USER_PASSWORD:?Must export USER_PASSWORD}"

RESOURCE_GROUP="dmplt-rg"
LOCATION="westus2"
ACR_NAME="dmpltacr"
CAE_NAME="dmplt-cae"
BACKEND_APP="dmplt-ca-backend"
POSTGRES_APP="dmplt-ca-postgres"
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

echo "=== [4/7] Creating PostgreSQL Container App ==="
az containerapp create \
  --name "$POSTGRES_APP" \
  --resource-group "$RESOURCE_GROUP" \
  --environment "$CAE_NAME" \
  --image postgres:16.1 \
  --ingress internal \
  --target-port 5432 \
  --transport tcp \
  --min-replicas 1 \
  --max-replicas 1 \
  --env-vars \
    POSTGRES_DB=data_mesh_plt \
    POSTGRES_USER=admin \
    "POSTGRES_PASSWORD=secretref:postgres-password" \
  --secrets "postgres-password=$POSTGRES_PASSWORD"

echo "=== [5/7] Creating Backend Container App ==="
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
    DB_HOST="$POSTGRES_APP" \
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

echo "=== [6/7] Creating Static Web App ==="
az staticwebapp create \
  --name "$STATIC_APP" \
  --resource-group "$RESOURCE_GROUP" \
  --location "$LOCATION"

echo "=== [7/7] Creating Service Principal for GitHub Actions ==="
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
echo "Secrets: POSTGRES_PASSWORD, ADMIN_PASSWORD, APP_USER_PASSWORD, USER_PASSWORD"
echo "  Values: the same passwords you exported before running this script"
echo ""
echo "Secret: CORS_ORIGINS"
echo "  Value: comma-separated list of allowed frontend origins (e.g. https://your-frontend.azurestaticapps.net)"
echo "============================================================"
