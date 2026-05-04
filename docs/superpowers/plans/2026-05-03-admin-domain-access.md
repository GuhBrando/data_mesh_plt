# Admin Domain Access Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Give PLATFORM_ADMIN users full owner-level controls on every domain, with a distinct blue "Admin" badge.

**Architecture:** Add `'admin'` to the `DomainAccess` union type; `getDomainAccess` short-circuits to `'admin'` when the caller is a PLATFORM_ADMIN. `DomainCard` renders the badge; `DomainPanel` gates controls on `access === 'owner' || access === 'admin'`. The backend already grants PLATFORM_ADMIN unrestricted access — this is a frontend-only change.

**Tech Stack:** React 18, TypeScript, Tailwind CSS, Vitest + @testing-library/react

---

## File Map

| File | Change |
|------|--------|
| `frontend/src/types/index.ts` | Add `'admin'` to `DomainAccess` union |
| `frontend/src/lib/domains.ts` | Add optional `userRole` param; short-circuit to `'admin'` for PLATFORM_ADMIN |
| `frontend/src/lib/domains.test.ts` | Add tests for the `'admin'` short-circuit |
| `frontend/src/pages/Domains/DomainCard.tsx` | Add `'admin'` entries to the three lookup maps |
| `frontend/src/pages/Domains/DomainCard.test.tsx` | Add test for `'admin'` badge rendering |
| `frontend/src/pages/Domains/DomainPanel.tsx` | `isOwner` includes `'admin'` |
| `frontend/src/pages/Domains/index.tsx` | Pass `user.role` to `getDomainAccess`; add `'admin'` to `FILTER_LABELS` and `filterTabs` |

---

## Task 1: Extend `DomainAccess` type and update `getDomainAccess`

**Files:**
- Modify: `frontend/src/types/index.ts`
- Modify: `frontend/src/lib/domains.ts`
- Modify: `frontend/src/lib/domains.test.ts`

- [ ] **Step 1: Add the new tests**

Open `frontend/src/lib/domains.test.ts` and append these three cases inside the existing `describe('getDomainAccess', ...)` block (after the last `it(...)` call, before the closing `}`):

```ts
it('returns "admin" for a PLATFORM_ADMIN regardless of domain membership', () => {
  expect(getDomainAccess(domain, 'user-dave', 'PLATFORM_ADMIN')).toBe('admin')
})

it('returns "admin" for a PLATFORM_ADMIN even when they are the domain owner', () => {
  expect(getDomainAccess(domain, 'user-alice', 'PLATFORM_ADMIN')).toBe('admin')
})

it('returns "owner" without userRole argument (backward-compatible)', () => {
  expect(getDomainAccess(domain, 'user-alice')).toBe('owner')
})
```

- [ ] **Step 2: Run the new tests to confirm they fail**

```bash
cd frontend
npx vitest run src/lib/domains.test.ts
```

Expected: the three new tests FAIL with `Expected: "admin" / Received: "owner"` or similar. The existing tests still pass.

- [ ] **Step 3: Extend `DomainAccess` in the types file**

Open `frontend/src/types/index.ts`. Change line 89:

```ts
// before
export type DomainAccess = 'owner' | 'maintainer' | 'member' | 'none'

// after
export type DomainAccess = 'admin' | 'owner' | 'maintainer' | 'member' | 'none'
```

- [ ] **Step 4: Update `getDomainAccess`**

Replace the entire contents of `frontend/src/lib/domains.ts` with:

```ts
import type { DomainWithMembers, DomainAccess } from '../types'

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

- [ ] **Step 5: Run all `domains.test.ts` tests to confirm they all pass**

```bash
cd frontend
npx vitest run src/lib/domains.test.ts
```

Expected: all 8 tests PASS.

- [ ] **Step 6: Commit**

```bash
git add frontend/src/types/index.ts frontend/src/lib/domains.ts frontend/src/lib/domains.test.ts
git commit -m "feat: add 'admin' DomainAccess value for PLATFORM_ADMIN users"
```

---

## Task 2: Update `DomainCard` to render the Admin badge

**Files:**
- Modify: `frontend/src/pages/Domains/DomainCard.tsx`
- Modify: `frontend/src/pages/Domains/DomainCard.test.tsx`

- [ ] **Step 1: Add the failing test**

Open `frontend/src/pages/Domains/DomainCard.test.tsx`. Append this case inside the existing `describe('DomainCard', ...)` block:

```tsx
it('renders "Admin" badge when access is admin', () => {
  render(<DomainCard domain={domain} access="admin" isSelected={false} onClick={vi.fn()} />)
  expect(screen.getByText('Admin')).toBeInTheDocument()
  expect(screen.getByTestId('domain-card')).toHaveAttribute('data-access', 'admin')
})
```

- [ ] **Step 2: Run the test to confirm it fails**

```bash
cd frontend
npx vitest run src/pages/Domains/DomainCard.test.tsx
```

Expected: the new test FAILS (TypeScript error — `'admin'` not assignable to `DomainAccess`, or runtime error on missing map key).

- [ ] **Step 3: Update the three lookup maps in `DomainCard.tsx`**

Replace the three `const` declarations at the top of `frontend/src/pages/Domains/DomainCard.tsx` with:

```ts
const ACCESS_CARD_CLASSES: Record<DomainAccess, string> = {
  admin:
    'border-[1.5px] border-blue-500 bg-blue-50 dark:bg-blue-900/20 dark:border-blue-400',
  owner:
    'border-[1.5px] border-indigo-500 bg-indigo-50 dark:bg-indigo-900/20 dark:border-indigo-400',
  maintainer:
    'border-[1.5px] border-amber-400 bg-amber-50 dark:bg-amber-900/20 dark:border-amber-400',
  member:
    'border-[1.5px] border-green-500 bg-green-50 dark:bg-green-900/20 dark:border-green-400',
  none: 'border border-slate-200 bg-slate-50 dark:bg-slate-800/50 dark:border-slate-700 opacity-65',
}

const ACCESS_BADGE_VARIANT: Record<DomainAccess, 'blue' | 'purple' | 'yellow' | 'green' | 'gray'> = {
  admin: 'blue',
  owner: 'purple',
  maintainer: 'yellow',
  member: 'green',
  none: 'gray',
}

const ACCESS_LABELS: Record<DomainAccess, string> = {
  admin: 'Admin',
  owner: 'Owner',
  maintainer: 'Maintainer',
  member: 'Member',
  none: 'No Access',
}
```

- [ ] **Step 4: Run all `DomainCard.test.tsx` tests to confirm they all pass**

```bash
cd frontend
npx vitest run src/pages/Domains/DomainCard.test.tsx
```

Expected: all 10 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/pages/Domains/DomainCard.tsx frontend/src/pages/Domains/DomainCard.test.tsx
git commit -m "feat: render Admin badge on DomainCard for admin access"
```

---

## Task 3: Update `DomainPanel` permission gates

**Files:**
- Modify: `frontend/src/pages/Domains/DomainPanel.tsx`

- [ ] **Step 1: Update `isOwner` in `PanelContent`**

Open `frontend/src/pages/Domains/DomainPanel.tsx`. In the `PanelContent` function, find this line:

```ts
const isOwner = access === 'owner'
```

Replace it with:

```ts
const isOwner = access === 'owner' || access === 'admin'
```

`canSeeMembers` on the next line (`access !== 'none'`) does not need changing — `'admin'` already passes that check.

- [ ] **Step 2: Run the full test suite to catch any regressions**

```bash
cd frontend
npm test
```

Expected: all tests PASS.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/pages/Domains/DomainPanel.tsx
git commit -m "feat: grant admin access full owner-level controls in DomainPanel"
```

---

## Task 4: Pass `user.role` in the Domains page and wire up the Admin filter tab

**Files:**
- Modify: `frontend/src/pages/Domains/index.tsx`

- [ ] **Step 1: Update `domainsWithAccess` to pass `user.role`**

Open `frontend/src/pages/Domains/index.tsx`. In the `domainsWithAccess` memo, change:

```ts
// before
access: user ? getDomainAccess(d, user.id) : ('none' as DomainAccess),

// after
access: user ? getDomainAccess(d, user.id, user.role) : ('none' as DomainAccess),
```

- [ ] **Step 2: Add `'admin'` to `FILTER_LABELS`**

Find `FILTER_LABELS` near the top of the file:

```ts
// before
const FILTER_LABELS: Record<FilterTab, string> = {
  all: 'All',
  owner: 'Owner',
  maintainer: 'Maintainer',
  member: 'Member',
}

// after
const FILTER_LABELS: Record<FilterTab, string> = {
  all: 'All',
  admin: 'Admin',
  owner: 'Owner',
  maintainer: 'Maintainer',
  member: 'Member',
}
```

- [ ] **Step 3: Add `'admin'` entry to the `filterTabs` array**

Find the `filterTabs` memo and add the `'admin'` entry after `'all'`:

```ts
// before
const filterTabs = useMemo(
  () => [
    { id: 'all' as FilterTab, label: 'All', count: domains.length },
    { id: 'owner' as FilterTab, label: 'Owner', count: counts.owner ?? 0 },
    { id: 'maintainer' as FilterTab, label: 'Maintainer', count: counts.maintainer ?? 0 },
    { id: 'member' as FilterTab, label: 'Member', count: counts.member ?? 0 },
  ],
  [counts, domains.length],
)

// after
const filterTabs = useMemo(
  () => [
    { id: 'all' as FilterTab, label: 'All', count: domains.length },
    { id: 'admin' as FilterTab, label: 'Admin', count: counts.admin ?? 0 },
    { id: 'owner' as FilterTab, label: 'Owner', count: counts.owner ?? 0 },
    { id: 'maintainer' as FilterTab, label: 'Maintainer', count: counts.maintainer ?? 0 },
    { id: 'member' as FilterTab, label: 'Member', count: counts.member ?? 0 },
  ],
  [counts, domains.length],
)
```

Non-admin users always have `counts.admin === undefined`, so `counts.admin ?? 0` is 0 and the existing `t.count > 0 || t.id === 'all'` guard hides the tab automatically.

- [ ] **Step 4: Run the full test suite**

```bash
cd frontend
npm test
```

Expected: all tests PASS.

- [ ] **Step 5: TypeScript check**

```bash
cd frontend
npx tsc --noEmit
```

Expected: no errors.

- [ ] **Step 6: Commit**

```bash
git add frontend/src/pages/Domains/index.tsx
git commit -m "feat: wire admin role into Domains page filter tabs and access computation"
```
