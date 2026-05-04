# Admin Domain Access — Design Spec

**Date:** 2026-05-03
**Status:** Approved

## Problem

PLATFORM_ADMIN users need full owner-level access to every domain: view members, add/remove members, and edit domain info. Currently `getDomainAccess` only checks `owner_id` and `members`, so an admin with no domain membership sees `'none'` and all management controls are hidden.

The backend already grants PLATFORM_ADMIN unrestricted access to all domain endpoints — the gap is purely frontend.

## Approach

Add `'admin'` as a first-class value in `DomainAccess`. `getDomainAccess` accepts the caller's role and short-circuits to `'admin'` for PLATFORM_ADMIN before any membership check. Components treat `'admin'` identically to `'owner'` for permission gates, but render a distinct badge.

## Type Change

```ts
// frontend/src/types/index.ts
export type DomainAccess = 'admin' | 'owner' | 'maintainer' | 'member' | 'none'
```

## Access Helper

```ts
// frontend/src/lib/domains.ts
export function getDomainAccess(
  domain: DomainWithMembers,
  userId: string,
  userRole?: string,
): DomainAccess {
  if (userRole === 'PLATFORM_ADMIN') return 'admin'
  if (domain.owner_id === userId) return 'owner'
  const member = domain.members.find((m) => m.user_id === userId)
  if (!member) return 'none'
  return member.role
}
```

`userRole` is optional so existing call sites that don't pass it continue to work (they just never get `'admin'`).

## Domains Page

- Pass `user.role` as the third argument to `getDomainAccess` in the `domainsWithAccess` memo.
- Add `'admin'` to `FILTER_LABELS`: `admin: 'Admin'`.
- `FilterTab` is derived from `DomainAccess` via `Exclude<DomainAccess, 'none'>`, so it picks up `'admin'` automatically. Non-admin users always have an `'admin'` count of 0, so the tab is filtered out and never rendered for them.

## DomainCard

Three lookup maps gain an `'admin'` entry:

| Map | Value |
|-----|-------|
| `ACCESS_BADGE_VARIANT` | `'blue'` (distinct from owner `'purple'`) |
| `ACCESS_CARD_CLASSES` | selected/hover styling consistent with other entries |
| `ACCESS_LABELS` | `'Admin'` |

## DomainPanel

```ts
const isOwner = access === 'owner' || access === 'admin'
const canSeeMembers = access !== 'none'  // unchanged
```

`isOwner` gates: edit domain button, add-member button, remove-member buttons. With `'admin'` included, admins see all of these.

## Scope

- **5 files changed**, all frontend.
- **No backend changes** — PLATFORM_ADMIN already bypasses ownership checks in all domain router endpoints.
- **No Profile admin section changes** — that UI is separately gated by `isAdmin` and does not use `getDomainAccess`.

## Files

| File | Change |
|------|--------|
| `frontend/src/types/index.ts` | Add `'admin'` to `DomainAccess` union |
| `frontend/src/lib/domains.ts` | Add `userRole` param, short-circuit for PLATFORM_ADMIN |
| `frontend/src/pages/Domains/index.tsx` | Pass `user.role`; add `'admin'` to `FILTER_LABELS` |
| `frontend/src/pages/Domains/DomainCard.tsx` | Add `'admin'` entries to the three lookup maps |
| `frontend/src/pages/Domains/DomainPanel.tsx` | `isOwner` includes `'admin'` |
