#!/usr/bin/env bash
# Grants the Databricks ACCOUNT ADMIN role to the dmplt-admin service principal via
# the account SCIM API, driven by the Databricks CLI.
#
# This is the ONE grant Terraform cannot do: the databricks provider's
# access_control_rule_set exposes no `account_admin` role. SCIM (this CLI path) does
# — additively, so it never manages/clobbers a list of other admins.
#
# Run ONCE by an existing Databricks account admin (an Azure AD Global Administrator
# is one implicitly). Idempotent: a no-op if the SP is already an account admin.
#
# Prereqs:
#   - az CLI, logged in as a Global Administrator   (az login)
#   - databricks CLI                                (https://docs.databricks.com/dev-tools/cli/install.html)
#   - jq
#
# Usage:
#   bash grant-account-admin.sh
#   ACCOUNT_ID=<id> APP_ID=<app-id> bash grant-account-admin.sh   # override autodetection

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Token audience for Databricks. This is the Application ID of the first-party
# "AzureDatabricks" app — a FIXED, GLOBAL constant present in every Azure AD tenant
# (not specific to this tenant). Verify with:
#   az ad sp show --id 2ff814a6-3304-4ab8-85cb-cd0e6f879c1d --query displayName -o tsv
# (returns "AzureDatabricks"). The az token must target this resource or Databricks
# rejects it.
DATABRICKS_RESOURCE="2ff814a6-3304-4ab8-85cb-cd0e6f879c1d"

# --- resolve inputs (env overrides; otherwise read from Terraform) ---------------
# admin SP application/client id comes from the platform stack output.
APP_ID="${APP_ID:-$(terraform -chdir="$SCRIPT_DIR/../platform" output -raw admin_client_id)}"
ACCOUNT_ID="${ACCOUNT_ID:-${DATABRICKS_ACCOUNT_ID:-}}"
if [[ -z "$ACCOUNT_ID" ]]; then
  echo "ERROR: set ACCOUNT_ID (or DATABRICKS_ACCOUNT_ID) — the Databricks Account ID." >&2
  exit 1
fi

# --- prereq checks ---------------------------------------------------------------
for bin in az databricks jq; do
  command -v "$bin" >/dev/null 2>&1 || { echo "ERROR: '$bin' not found in PATH." >&2; exit 1; }
done

# --- authenticate the Databricks CLI to the account with an Azure CLI token -------
echo "==> Acquiring an Azure AD token for Databricks (as the logged-in az identity)..."
DATABRICKS_TOKEN="$(az account get-access-token --resource "$DATABRICKS_RESOURCE" --query accessToken -o tsv)"
export DATABRICKS_TOKEN
export DATABRICKS_HOST="https://accounts.azuredatabricks.net"
export DATABRICKS_ACCOUNT_ID="$ACCOUNT_ID"

# Account-level SCIM operations go through the CLI's typed `account` commands. (The
# generic `databricks api` command targets the workspace host and returns HTML for
# account paths, so it is not used here.)

# --- find the SP's account id by applicationId -----------------------------------
echo "==> Looking up service principal $APP_ID ..."
SP_ID="$(databricks account service-principals list -o json \
  | jq -r --arg app "$APP_ID" '.[] | select(.applicationId==$app) | .id')"

if [[ -z "$SP_ID" || "$SP_ID" == "null" ]]; then
  echo "ERROR: SP $APP_ID is not registered in the account." >&2
  echo "       Apply the databricks_bootstrap stack first (it registers the SP)." >&2
  exit 1
fi
echo "    account SP id: $SP_ID"

# --- idempotency: already an account admin? --------------------------------------
ALREADY="$(databricks account service-principals get "$SP_ID" -o json \
  | jq -r '[.roles[]?.value] | index("account_admin") // empty')"
if [[ -n "$ALREADY" ]]; then
  echo "==> dmplt-admin is already an account admin. Nothing to do."
  exit 0
fi

# --- grant account_admin (additive PATCH) ----------------------------------------
echo "==> Granting account_admin ..."
databricks account service-principals patch "$SP_ID" --json '{
  "schemas": ["urn:ietf:params:scim:api:messages:2.0:PatchOp"],
  "Operations": [{ "op": "add", "path": "roles", "value": [{ "value": "account_admin" }] }]
}' >/dev/null

# --- verify ----------------------------------------------------------------------
VERIFY="$(databricks account service-principals get "$SP_ID" -o json \
  | jq -r '[.roles[]?.value] | index("account_admin") // empty')"
if [[ -n "$VERIFY" ]]; then
  echo "==> OK: dmplt-admin ($APP_ID) is now a Databricks account admin."
else
  echo "WARNING: PATCH sent but verification did not show account_admin. Check the Account Console." >&2
  exit 1
fi
