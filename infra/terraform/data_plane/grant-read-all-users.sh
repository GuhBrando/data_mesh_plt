#!/usr/bin/env bash
# Grants READ access to ALL account users (the built-in "account users" group) on
# every Unity Catalog catalog created by this stack: USE_CATALOG + USE_SCHEMA +
# SELECT. These are inherited by every schema/table in the catalog, so it covers
# reading data.
#
# The catalogs are owned by the dmplt-admin service principal, so this routine
# authenticates AS that SP (client id/secret from the platform stack) to apply the
# grants. Additive and idempotent — re-running is safe and never removes other
# grants.
#
# Prereqs: az (logged in), the Databricks CLI, jq, terraform.
#
# Usage (from infra/terraform/data_plane):
#   bash grant-read-all-users.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLATFORM_DIR="$SCRIPT_DIR/../platform"
# AzureDatabricks first-party app id — the token audience (fixed, global constant).
DATABRICKS_RESOURCE="2ff814a6-3304-4ab8-85cb-cd0e6f879c1d"
GROUP="account users" # built-in group that contains every user in the account
PRIVILEGES='["USE_CATALOG","USE_SCHEMA","SELECT"]'

for bin in az databricks jq terraform; do
  command -v "$bin" >/dev/null 2>&1 || { echo "ERROR: '$bin' not found in PATH." >&2; exit 1; }
done

# --- inputs from Terraform state ------------------------------------------------
# tr -d '\r' guards against CRLF that Windows builds of terraform/jq can emit, which
# would otherwise sneak a carriage return into URLs and tokens.
CLIENT_ID="$(terraform -chdir="$PLATFORM_DIR" output -raw admin_client_id | tr -d '\r\n')"
CLIENT_SECRET="$(terraform -chdir="$PLATFORM_DIR" output -raw admin_client_secret | tr -d '\r\n')"
WORKSPACE_URL="$(terraform -chdir="$PLATFORM_DIR" output -raw workspace_url | tr -d '\r\n')"
TENANT_ID="${TENANT_ID:-$(az account show --query tenantId -o tsv | tr -d '\r\n')}"
CATALOGS="$(terraform -chdir="$SCRIPT_DIR" output -json catalog_names | jq -r '.[]' | tr -d '\r')"

# --- authenticate as dmplt-admin (the catalog owner) via client credentials -----
echo "==> Acquiring token as dmplt-admin..."
SP_TOKEN="$(curl -s -X POST "https://login.microsoftonline.com/$TENANT_ID/oauth2/v2.0/token" \
  -d "client_id=$CLIENT_ID" \
  -d "client_secret=$CLIENT_SECRET" \
  -d "grant_type=client_credentials" \
  -d "scope=$DATABRICKS_RESOURCE/.default" | jq -r '.access_token')"
[[ -n "$SP_TOKEN" && "$SP_TOKEN" != "null" ]] || { echo "ERROR: failed to acquire SP token." >&2; exit 1; }

export DATABRICKS_HOST="$WORKSPACE_URL"
export DATABRICKS_TOKEN="$SP_TOKEN"

# --- grant read to all account users on each catalog ----------------------------
for cat in $CATALOGS; do
  echo "==> Granting read on catalog '$cat' to '$GROUP'..."
  databricks grants update catalog "$cat" \
    --json "{\"changes\":[{\"principal\":\"$GROUP\",\"add\":$PRIVILEGES}]}" >/dev/null
done

echo "==> Done. All account users now have read on: $(echo "$CATALOGS" | tr '\n' ' ')"
