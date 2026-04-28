# Data Mesh Platform

A platform for managing data products, data contracts, and data governance across domains. Built with FastAPI (Python) on the backend and React + TypeScript on the frontend.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | FastAPI, Python 3.12+, asyncpg |
| Frontend | React 18, TypeScript, Vite, Tailwind CSS |
| Database | PostgreSQL (Atlas migrations) |
| Auth | JWT (access + refresh tokens), bcrypt |
| Testing | pytest, Vitest |

---

## Project Structure

```
├── backend/          # FastAPI application (Clean Architecture)
│   ├── domain/       # Entities, interfaces, value objects
│   ├── use_cases/    # Application logic
│   ├── interface/    # Routers, schemas, security, dependencies
│   └── infra/        # Repositories, config, DB connection
├── frontend/         # React + TypeScript SPA
│   └── src/
│       ├── components/
│       ├── contexts/
│       ├── pages/
│       └── lib/
├── database/
│   ├── migrations/   # SQL migration files (Atlas)
│   └── schema/       # HCL schema definitions
└── docs/
    └── superpowers/
        ├── specs/    # Design documents
        └── plans/    # Implementation plans
```

---

## Authentication

Authentication uses JWT with an access token (15 min) and a refresh token (7 days). The frontend stores tokens in localStorage and automatically refreshes the access token before it expires.

- Login: `POST /api/v1/auth/login`
- Refresh: `POST /api/v1/auth/refresh`
- Logout: `POST /api/v1/auth/logout` (revokes refresh token)

---

## Role-Based Access Control (RBAC)

### Roles

Every user has a single platform-level role. New users receive **Data Consumer** by default.

| Role | Description |
|---|---|
| **Platform Admin** | Full access to all resources and operations across the platform |
| **Data Owner** | Full control within their domain — manages members, approves/rejects contracts |
| **Data Steward** | Creates and edits data contracts within their domain; assigns contract stakeholders |
| **Data Consumer** | Read-only access to published resources *(default for new registrations)* |

### Domains

A domain is a namespace. Users belong to one or more domains via domain membership. A user's platform role applies within each domain they are a member of. The first Data Owner for a domain is always assigned by a Platform Admin; after that, Data Owners manage their own domain membership.

### Stakeholders

A Stakeholder is not a platform role — it is a per-contract relationship. A Data Steward can assign any user as a Stakeholder on a specific data contract, granting them read access to drafts and improving cross-domain communication and contract consistency.

### Permission Matrix

#### User Management

| Action | Platform Admin | Data Owner | Data Steward | Data Consumer |
|---|---|---|---|---|
| Delete user from platform | ✅ | ❌ | ❌ | ❌ |
| Assign platform role to any user | ✅ | ❌ | ❌ | ❌ |
| Assign first Data Owner to a domain | ✅ | ❌ | ❌ | ❌ |
| Add/remove members from own domain | ✅ | ✅ own domain | ❌ | ❌ |
| View own profile | ✅ | ✅ | ✅ | ✅ |

#### Data Contracts

| Action | Platform Admin | Data Owner | Data Steward | Data Consumer |
|---|---|---|---|---|
| Create contract | ✅ | ❌ | ✅ own domain | ❌ |
| Edit contract | ✅ | ❌ | ✅ own domain | ❌ |
| Approve / reject contract | ✅ | ✅ own domain | ❌ | ❌ |
| Delete contract | ✅ | ✅ own domain | ❌ | ❌ |
| Read published contracts | ✅ | ✅ | ✅ | ✅ |
| Read draft contracts | ✅ | ✅ own domain | ✅ own domain | ❌ |
| Read draft contracts (as Stakeholder) | — | — | — | ✅ assigned contracts |
| Assign stakeholders to a contract | ✅ | ❌ | ✅ own domain | ❌ |

---

## Running Locally

### Backend

```bash
cd backend
python -m uvicorn main:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

### Database migrations

```bash
atlas migrate apply --env local
```

---

## Docs

- [RBAC Design](docs/superpowers/specs/2026-04-28-rbac-design.md)
- [Auth Security Roadmap](docs/security/auth-security-roadmap.md)
