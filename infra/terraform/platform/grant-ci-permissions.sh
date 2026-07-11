#!/usr/bin/env bash
# Grants the standing permissions that let GitHub Actions run the platform stack as
# the dmplt-devops service principal (OIDC), and lets human operators use the
# Azure AD-authenticated state backend.
#
# These are the grants Terraform cannot express in this stack:
#   - Storage Blob Data Contributor on the tfstate storage account must exist BEFORE
#     `terraform init` can read state (chicken-and-egg with the stack itself).
#   - dmplt-devops owning its OWN application/service principal is a dependency cycle
#     in HCL, and the standalone azuread_application_owner resource is incompatible
#     with the azuread_application resource this stack uses.
#   - The Microsoft Graph app role (Application.ReadWrite.OwnedBy) is admin consent,
#     which only a privileged human can grant.
#
# Grants (all least-privilege):
#   1. Signed-in user  -> Storage Blob Data Contributor on dmplttfstate
#   2. dmplt-devops SP -> Storage Blob Data Contributor on dmplttfstate
#   3. dmplt-devops SP -> Graph app role Application.ReadWrite.OwnedBy (admin consent)
#   4. dmplt-devops SP -> owner of the dmplt-admin and dmplt-devops apps and SPs
#   5. GitHub repository variables AZURE_CLIENT_ID / AZURE_TENANT_ID /
#      AZURE_SUBSCRIPTION_ID (consumed by .github/workflows/infra.yml)
#
# Run ONCE by an Owner + Global Administrator identity (az login). Idempotent: every
# grant is checked before it is made. If the platform stack has not been applied yet
# (dmplt-devops missing), only grant 1 is made — re-run after `terraform apply`.
#
# Prereqs: az CLI (logged in); gh CLI (logged in) for step 5. Run in Git Bash on
# Windows.
#
# Usage:
#   bash grant-ci-permissions.sh
#   AZURE_SUBSCRIPTION_ID=<id> AZURE_TENANT_ID=<id> bash grant-ci-permissions.sh  # override az session

set -euo pipefail

# Git Bash mangles arguments that start with "/" into Windows paths; --scope values
# like /subscriptions/... must reach az verbatim.
export MSYS_NO_PATHCONV=1

command -v az >/dev/null 2>&1 || { echo "ERROR: 'az' not found in PATH." >&2; exit 1; }

BLOB_ROLE="Storage Blob Data Contributor"
GRAPH_APP_ID="00000003-0000-0000-c000-000000000000" # Microsoft Graph (fixed, global)
GRAPH_ROLE="Application.ReadWrite.OwnedBy"

# --- resolve inputs (local env overrides; otherwise read from the az session) -------
SUB_ID="${AZURE_SUBSCRIPTION_ID:-$(az account show --query id -o tsv)}"
TENANT_ID="${AZURE_TENANT_ID:-$(az account show --query tenantId -o tsv)}"
TFSTATE_SCOPE="/subscriptions/$SUB_ID/resourceGroups/dmplt-tfstate-rg/providers/Microsoft.Storage/storageAccounts/dmplttfstate"
USER_OBJ_ID="$(az ad signed-in-user show --query id -o tsv)"
echo "==> Subscription $SUB_ID, signed-in user $USER_OBJ_ID"

# has_role <principal-object-id>
has_role() {
  [[ -n "$(az role assignment list --assignee "$1" --role "$BLOB_ROLE" --scope "$TFSTATE_SCOPE" --query "[0].id" -o tsv)" ]]
}

# grant_blob_role <principal-object-id> <principal-type> <label>
grant_blob_role() {
  if has_role "$1"; then
    echo "==> $3 already has '$BLOB_ROLE' on dmplttfstate. Nothing to do."
  else
    echo "==> Granting '$BLOB_ROLE' on dmplttfstate to $3 ..."
    az role assignment create --assignee-object-id "$1" --assignee-principal-type "$2" \
      --role "$BLOB_ROLE" --scope "$TFSTATE_SCOPE" >/dev/null
  fi
}

# --- 1. operator: blob access to the state backend (use_azuread_auth) ---------------
grant_blob_role "$USER_OBJ_ID" "User" "the signed-in user"

# --- locate dmplt-devops (created by this stack's identities module) ----------------
DEVOPS_SP_ID="$(az ad sp list --display-name dmplt-devops --query "[0].id" -o tsv)"
if [[ -z "$DEVOPS_SP_ID" ]]; then
  echo "==> dmplt-devops SP not found: the platform stack hasn't been applied yet."
  echo "    Operator grant done. Re-run this script after 'terraform apply' to grant CI."
  exit 0
fi
DEVOPS_APP_OBJ_ID="$(az ad app list --display-name dmplt-devops --query "[0].id" -o tsv)"
ADMIN_APP_OBJ_ID="$(az ad app list --display-name dmplt-admin --query "[0].id" -o tsv)"
ADMIN_SP_ID="$(az ad sp list --display-name dmplt-admin --query "[0].id" -o tsv)"
echo "==> dmplt-devops SP $DEVOPS_SP_ID, dmplt-admin SP $ADMIN_SP_ID"

# --- 2. CI: blob access to the state backend ----------------------------------------
grant_blob_role "$DEVOPS_SP_ID" "ServicePrincipal" "dmplt-devops"

# --- 3. CI: Graph Application.ReadWrite.OwnedBy (manage the apps it owns) -----------
GRAPH_SP_ID="$(az ad sp show --id "$GRAPH_APP_ID" --query id -o tsv)"
ROLE_ID="$(az ad sp show --id "$GRAPH_APP_ID" --query "appRoles[?value=='$GRAPH_ROLE'].id | [0]" -o tsv)"
ASSIGNED="$(az rest --method GET \
  --uri "https://graph.microsoft.com/v1.0/servicePrincipals/$DEVOPS_SP_ID/appRoleAssignments" \
  --query "value[?appRoleId=='$ROLE_ID'].id | [0]" -o tsv)"
if [[ -n "$ASSIGNED" ]]; then
  echo "==> dmplt-devops already has $GRAPH_ROLE. Nothing to do."
else
  echo "==> Granting Graph app role $GRAPH_ROLE to dmplt-devops (admin consent) ..."
  az rest --method POST \
    --uri "https://graph.microsoft.com/v1.0/servicePrincipals/$DEVOPS_SP_ID/appRoleAssignments" \
    --body "{\"principalId\":\"$DEVOPS_SP_ID\",\"resourceId\":\"$GRAPH_SP_ID\",\"appRoleId\":\"$ROLE_ID\"}" >/dev/null
fi

# --- 4. CI: ownership of both apps and SPs (OwnedBy only covers owned objects) ------
# ensure_owner <applications|servicePrincipals> <object-id> <label>
ensure_owner() {
  local existing
  existing="$(az rest --method GET --uri "https://graph.microsoft.com/v1.0/$1/$2/owners" \
    --query "value[?id=='$DEVOPS_SP_ID'].id | [0]" -o tsv)"
  if [[ -n "$existing" ]]; then
    echo "==> dmplt-devops already owns $3. Nothing to do."
  else
    echo "==> Adding dmplt-devops as owner of $3 ..."
    az rest --method POST --uri "https://graph.microsoft.com/v1.0/$1/$2/owners/\$ref" \
      --body "{\"@odata.id\":\"https://graph.microsoft.com/v1.0/directoryObjects/$DEVOPS_SP_ID\"}" >/dev/null
  fi
}

ensure_owner applications      "$ADMIN_APP_OBJ_ID"  "the dmplt-admin application"
ensure_owner applications      "$DEVOPS_APP_OBJ_ID" "its own application"
ensure_owner servicePrincipals "$ADMIN_SP_ID"       "the dmplt-admin service principal"
ensure_owner servicePrincipals "$DEVOPS_SP_ID"      "its own service principal"

# --- 5. GitHub repository variables (identifiers, not secrets) ----------------------
DEVOPS_CLIENT_ID="$(az ad sp show --id "$DEVOPS_SP_ID" --query appId -o tsv)"
if command -v gh >/dev/null 2>&1 && gh auth status >/dev/null 2>&1; then
  echo "==> Setting GitHub repository variables (AZURE_CLIENT_ID / _TENANT_ID / _SUBSCRIPTION_ID) ..."
  gh variable set AZURE_CLIENT_ID --body "$DEVOPS_CLIENT_ID"
  gh variable set AZURE_TENANT_ID --body "$TENANT_ID"
  gh variable set AZURE_SUBSCRIPTION_ID --body "$SUB_ID"
else
  echo "WARNING: gh CLI missing or not authenticated — set the repository variables by hand:" >&2
  echo "  gh variable set AZURE_CLIENT_ID       --body $DEVOPS_CLIENT_ID" >&2
  echo "  gh variable set AZURE_TENANT_ID       --body $TENANT_ID" >&2
  echo "  gh variable set AZURE_SUBSCRIPTION_ID --body $SUB_ID" >&2
fi

echo "==> OK: CI (dmplt-devops) can now run the platform stack via OIDC."
