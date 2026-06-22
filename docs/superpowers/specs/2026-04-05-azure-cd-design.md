# Azure CD Pipeline — Design Spec

**Date:** 2026-04-05
**Author:** GuhBrando
**Status:** Approved

---

## Overview

Continuous Deployment pipeline for the Data Mesh Platform to Azure, triggered by version tags (`v*.*.*`). Uses GitHub Actions with Azure CLI. Infrastructure is created once manually via a setup script; the pipeline only handles build and deploy.

**Phase:** Development / Staging
**Future migration:** PostgreSQL Container App → Azure Database for PostgreSQL Flexible Server (when moving to production)

---

## Architecture

```
Git tag v*.*.* pushed
        │
        ├──► Job: build-and-push-backend (ubuntu-latest)
        │         1. Login to dmpltacr (ACR)
        │         2. Build Docker image from ./dockerfile
        │         3. Push → dmpltacr.azurecr.io/backend:<tag> + :latest
        │                                                              │
        │                                                              ▼
        │                                                    Job: deploy-backend
        │                                                    az containerapp update
        │                                                    → dmplt-ca-backend
        │
        └──► Job: deploy-frontend (parallel)
                  1. Checkout
                  2. Azure/static-web-apps-deploy@v1
                     app_location: frontend
                     output_location: dist
                  → dmplt-stapp-frontend
```

---

## Azure Resources

| Resource | Name | Cost |
|---|---|---|
| Resource Group | `dmplt-rg` | Free |
| Container Registry (ACR) | `dmpltacr` | ~$5/month (Basic) |
| Container Apps Environment | `dmplt-cae` | Free |
| Container App — backend | `dmplt-ca-backend` | Pay-per-use |
| Container App — postgres | `dmplt-ca-postgres` | Pay-per-use |
| Static Web Apps | `dmplt-stapp-frontend` | Free (Free tier) |

**Location:** `brazilsouth`

---

## Files Created

| File | Purpose |
|---|---|
| `.github/workflows/cd.yml` | CD pipeline triggered on version tags |
| `scripts/azure-setup.sh` | One-time Azure resource provisioning script |

---

## Workflow: `.github/workflows/cd.yml`

**Trigger:** `push` to tags matching `v*.*.*`

**Jobs:**

### `build-and-push-backend`
- Logs into `dmpltacr` using `ACR_USERNAME` / `ACR_PASSWORD` secrets
- Builds the backend Docker image from `./dockerfile`
- Pushes two tags: `<git-tag>` and `latest`

### `deploy-frontend`
- Runs in parallel with `build-and-push-backend`
- Uses `Azure/static-web-apps-deploy@v1`
- Builds Vite app from `frontend/` directory, output to `dist/`
- Deploys to `dmplt-stapp-frontend`

### `deploy-backend`
- Depends on `build-and-push-backend`
- Authenticates to Azure via `AZURE_CREDENTIALS` (Service Principal)
- Runs `az containerapp update` with the new image tag

---

## GitHub Secrets Required

| Secret | How to obtain |
|---|---|
| `AZURE_CREDENTIALS` | Output of `az ad sp create-for-rbac --json-auth` in the setup script |
| `ACR_USERNAME` | Printed by setup script (`az acr credential show`) |
| `ACR_PASSWORD` | Printed by setup script (`az acr credential show`) |
| `AZURE_STATIC_WEB_APPS_API_TOKEN` | Printed by setup script (`az staticwebapp secrets list`) |
| `POSTGRES_PASSWORD` | Defined by the developer before running setup script |
| `ADMIN_PASSWORD` | Defined by the developer before running setup script |
| `APP_USER_PASSWORD` | Defined by the developer before running setup script |
| `USER_PASSWORD` | Defined by the developer before running setup script |

---

## Setup Script: `scripts/azure-setup.sh`

One-time script that provisions all Azure resources in order:

1. Resource Group (`dmplt-rg` in `brazilsouth`)
2. Container Registry (`dmpltacr`, Basic tier, admin enabled)
3. Container Apps Environment (`dmplt-cae`)
4. PostgreSQL Container App (`dmplt-ca-postgres`) — internal TCP ingress on port 5432, using `postgres:16.1` image
5. Backend Container App (`dmplt-ca-backend`) — external ingress on port 8000, placeholder image initially, configured with ACR credentials and DB env vars
6. Static Web App (`dmplt-stapp-frontend`)
7. Service Principal (`sp-dmplt-github-actions`) with Contributor role scoped to `dmplt-rg`
8. Prints all GitHub secret values to terminal

**Prerequisites before running:**
```bash
export POSTGRES_PASSWORD=<value>
export ADMIN_PASSWORD=<value>
export APP_USER_PASSWORD=<value>
export USER_PASSWORD=<value>
```

---

## PostgreSQL Networking

The backend Container App connects to PostgreSQL via `DB_HOST=dmplt-ca-postgres`. Within the same Container Apps Environment (`dmplt-cae`), the internal DNS resolves `dmplt-ca-postgres` to the PostgreSQL container using internal TCP ingress on port 5432.

**Note:** In this dev/staging phase, PostgreSQL data is ephemeral — a container restart loses all data. This is acceptable for development. Migration to Azure Database for PostgreSQL Flexible Server (Burstable B1ms, ~$12-15/month) is the planned path to production.

---

## Deploy Flow (after setup)

```bash
# Tag and push to trigger CD
git tag v0.1.0
git push origin v0.1.0
```

GitHub Actions will:
1. Build and push backend image to ACR
2. Deploy frontend to Static Web Apps
3. Update backend Container App with the new image

---

## Out of Scope

- Database migrations (Atlas) are not run in the CD pipeline — applied manually for now
- No rollback mechanism in this phase
- No staging vs. production environment split — single environment for dev/staging
- ~~No Bicep / IaC — infrastructure created manually via setup script~~ **Superseded 2026-06-22:** all infrastructure is now Terraform-managed under `infra/terraform/` (see `docs/superpowers/specs/2026-06-22-terraform-azure-databricks-design.md`). `scripts/azure-setup.sh` is **deprecated** and kept only as a manual fallback until the `terraform import` is verified against live Azure (zero destroy/replace on `terraform plan`); remove it after that verification.
