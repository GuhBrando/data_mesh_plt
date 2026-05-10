# Domains Feature Design

**Date:** 2026-05-03
**Status:** Approved
**Hierarchy:** Domain > Data Contract > Data Product

---

## Overview

Add a first-class Domains feature to the data mesh platform. Domains sit at the top of the data governance hierarchy and gate access to Data Contracts and Data Products. The feature has two surfaces:

1. **`/domains` page** — discoverable by all authenticated users; owners manage membership from here.
2. **Profile page admin panel** — PLATFORM_ADMIN-only tabs for domain lifecycle management (create, edit, delete, reassign owner).

---

## Data Model

### Domain (extended)

```typescript
interface Domain {
  id: string
  name: string
  description: string
  owner_id: string      // references User.id
  created_at: string
  updated_at: string
}
```

### DomainMember

```typescript
interface DomainMember {
  user_id: string
  username: string
  role: 'maintainer' | 'member'
}
```

### DomainWithMembers

```typescript
interface DomainWithMembers extends Domain {
  members: DomainMember[]
  contract_count: number   // denormalized count for card display
}
```

### UserDomainAccess (derived, frontend only)

```typescript
type DomainAccess = 'owner' | 'maintainer' | 'member' | 'none'
```

Computed on the frontend by comparing `domain.owner_id` and `domain.members[].user_id` against the current user.

---

## API Endpoints (frontend perspective)

| Method | Path | Who can call | Purpose |
|--------|------|-------------|---------|
| GET | `/domains` | All authenticated | List all domains with member counts and contract_count |
| GET | `/domains/:id` | All authenticated | Get domain + member list |
| POST | `/domains` | PLATFORM_ADMIN | Create domain |
| PUT | `/domains/:id` | PLATFORM_ADMIN, domain owner | Update name/description/owner |
| DELETE | `/domains/:id` | PLATFORM_ADMIN | Delete domain |
| POST | `/domains/:id/members` | Domain owner | Add member with role |
| PATCH | `/domains/:id/members/:userId` | Domain owner | Change member role |
| DELETE | `/domains/:id/members/:userId` | Domain owner | Remove member |

---

## Navigation

The `Domains` nav item is inserted **above Data Contracts** in both the sidebar and bottom nav.

**Sidebar order:** Dashboard → Domains → Data Contracts → Data Products → Users
**BottomNav order:** Dashboard → Domains → Data Contracts → Data Products → Users

Icon: building/domain icon (Lucide `Building2`).

---

## `/domains` Page

### Route
`/domains` — protected, all authenticated users.

### Layout

**Desktop (md+):**
- Page header with title and subtitle.
- Underline filter tabs: All · Owner · Member · Maintainer (each shows count).
- 3-column card grid (`grid-cols-3`). Clicking a card opens a **side panel** (fixed-width right column, ~280px).
- Side panel closes with ✕ or by clicking another card.

**Mobile (< md):**
- Horizontal scrollable filter **chips** (pill style) instead of underline tabs.
- 1-column card list.
- Clicking a card opens a **bottom sheet** that slides up (drag handle at top, covers ~70% of screen).

### Domain Cards

Access status drives visual treatment:

| Access | Border | Background | Badge color |
|--------|--------|-----------|-------------|
| Owner | 1.5px indigo-500 | indigo-50 | indigo filled |
| Maintainer | 1.5px amber-400 | amber-50 | amber filled |
| Member | 1.5px green-500 | green-50 | green filled |
| No Access | 1px gray-200 | gray-50, 65% opacity | gray muted |

Card content: name, description (truncated 2 lines), member count, contract count.

### Side Panel / Bottom Sheet

Shows for all access levels, but content is gated:

**No Access:** name, description, owner name only. No member list.

**Member / Maintainer:** name, description, owner name, member list (read-only, no remove buttons).

**Owner:** full panel — name, description, owner, member list with remove (✕) and role badge, `+ Add` button, `✏️ Edit Domain Info` button at bottom.

**Add Member flow:** clicking `+ Add` opens a small modal with a user search input (searches all platform users, filtered to exclude users already in the domain) and a role selector (Member / Maintainer). Submits `POST /domains/:id/members`.

**Edit Domain Info (owner):** opens a modal pre-filled with name and description. Submits `PUT /domains/:id`. Owner cannot reassign `owner_id` from this modal — that is admin-only.

---

## Profile Page — Admin Panel

### Who sees it
Only users with `role === 'PLATFORM_ADMIN'`. The admin section is completely hidden for all other roles.

### Desktop layout
The existing Profile sidebar nav gains a new **"Admin" section** with a red label and shield prefix, visually separated from the "Account" section:

```
Account
  My Role
  Change Password

🛡 Admin
  Domains          ← active
  Users            ← stubbed, future
```

### Mobile layout
The existing horizontal tab row gains admin tabs to the right, prefixed with 🛡 and using a red color. Tabs scroll horizontally.

### Domains Admin Tab

**Header:** "Manage Domains" title + subtitle + `+ New Domain` button (red).

**Table columns:** Name · Owner · Members · Contracts · Actions
**Actions per row:** `✏️ Edit` · `🗑 Delete`

**Create/Edit modal fields:**
- Name (required, text input)
- Description (required, textarea)
- Owner (required, user search — searches all platform users, shows username)

**Delete:** confirmation modal ("This will not delete associated contracts. Members will lose domain access.").

### Users Admin Tab (stubbed)
Renders a placeholder card: "User management coming soon." Tab is visible but content is a stub. Provides the extension point for future admin functions.

---

## Component Structure

```
src/
├── pages/
│   ├── Domains/
│   │   ├── index.tsx            # Page: filter tabs + card grid + panel state
│   │   ├── DomainCard.tsx       # Individual card (access-aware styling)
│   │   ├── DomainPanel.tsx      # Desktop side panel + mobile bottom sheet
│   │   └── AddMemberModal.tsx   # User search + role selector modal
│   └── Profile.tsx              # Extended: admin section added conditionally
│
├── hooks/
│   ├── useDomains.ts            # useAllDomains, useCreateDomain, useUpdateDomain, useDeleteDomain
│   └── useDomainMembers.ts      # useDomainMembers, useAddMember, useUpdateMember, useRemoveMember
│
└── types/index.ts               # Domain, DomainMember, DomainWithMembers types added
```

**Existing `useUserDomains` hook** — the Profile "My Role" tab's "Domain Memberships" section uses `useUserDomains(userId)` (fetches `GET /users/:id/domains`). This is unchanged. The new `useAllDomains` hook fetches `GET /domains` for the new page. They serve different purposes and coexist independently.

**Profile.tsx admin section** — rather than extracting to a separate file, the admin tabs (Domains, Users) are added as conditional sections inside the existing `Profile.tsx`, rendered only when `user.role === 'PLATFORM_ADMIN'`. This keeps the Profile page self-contained and avoids a proliferation of small files for what is currently 2 simple tab panels. If the admin section grows beyond ~150 lines it should be extracted to `pages/Profile/AdminPanel.tsx`.

**DomainPanel.tsx** — single component that renders as a side panel on `md+` and a bottom sheet on mobile using Tailwind responsive classes. The panel receives the selected domain + current user access level as props and gates UI accordingly.

---

## Permission Gates (frontend)

| Action | Gate |
|--------|------|
| View `/domains` page | Any authenticated user |
| See member list in panel | `access !== 'none'` |
| Add / remove members | `access === 'owner'` |
| Edit domain info (panel) | `access === 'owner'` |
| See Admin tabs in Profile | `user.role === 'PLATFORM_ADMIN'` |
| Create domain | `user.role === 'PLATFORM_ADMIN'` |
| Delete domain | `user.role === 'PLATFORM_ADMIN'` |
| Reassign domain owner | `user.role === 'PLATFORM_ADMIN'` (via edit modal in admin tab) |

Backend enforces all of these — frontend gates are UX-only.

---

## Responsive Breakpoints

| Element | Mobile (< md) | Desktop (md+) |
|---------|--------------|---------------|
| Filter controls | Scrollable pill chips | Underline tabs |
| Card grid | 1 column | 2 col (md) → 3 col (lg) |
| Domain detail | Bottom sheet (slides up, 70vh) | Side panel (fixed right column) |
| Profile nav | Horizontal scrollable tab row | Vertical sidebar with sections |

---

## Error Handling

- Failed domain fetch: inline error state with retry button (consistent with existing pages).
- Add/remove member failure: toast notification (reuse existing pattern).
- Delete domain with existing contracts: backend returns 409 — show error message "Cannot delete a domain with active contracts."
- Permission errors (403): toast "You don't have permission to perform this action."

---

## Non-goals (out of scope for this implementation)

- Domain-level filtering on the Data Contracts list page (separate future task).
- Domain analytics / usage dashboards in the admin panel.
- Bulk member import.
- Email notifications when added to a domain.
