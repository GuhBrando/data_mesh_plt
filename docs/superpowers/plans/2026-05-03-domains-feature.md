# Domains Feature Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a Domains page (`/domains`) above Data Contracts in navigation, plus an admin panel in the Profile page, implementing the full domain hierarchy (Domain > Data Contract > Data Product).

**Architecture:** A `/domains` route shows all domains as a card grid with a slide-in panel (desktop) or bottom sheet (mobile), gated by access level. The Profile page gains admin-only tabs (PLATFORM_ADMIN role) for domain lifecycle management. Domain access is computed on the frontend via a pure `getDomainAccess` helper, while all enforcement lives in the backend.

**Tech Stack:** React 18 + TypeScript, Vite, React Query v5, React Router v6, Tailwind CSS, Lucide React, Vitest + @testing-library/react.

---

## File Map

| Action | Path | Responsibility |
|--------|------|----------------|
| Modify | `frontend/src/types/index.ts` | Replace minimal `Domain`, add `DomainMember`, `DomainWithMembers`, `DomainAccess` |
| Create | `frontend/src/lib/domains.ts` | Pure `getDomainAccess` helper |
| Create | `frontend/src/lib/domains.test.ts` | Tests for `getDomainAccess` |
| Create | `frontend/src/hooks/useDomains.ts` | `useAllDomains`, `useCreateDomain`, `useUpdateDomain`, `useDeleteDomain` |
| Create | `frontend/src/hooks/useDomainMembers.ts` | `useAddDomainMember`, `useUpdateDomainMember`, `useRemoveDomainMember` |
| Modify | `frontend/src/components/Sidebar.tsx` | Insert Domains nav item above Data Contracts |
| Modify | `frontend/src/components/BottomNav.tsx` | Insert Domains nav item above Data Contracts |
| Modify | `frontend/src/App.tsx` | Add `/domains` route |
| Create | `frontend/src/pages/Domains/DomainCard.tsx` | Access-aware domain card |
| Create | `frontend/src/pages/Domains/DomainCard.test.tsx` | Card rendering tests |
| Create | `frontend/src/pages/Domains/AddMemberModal.tsx` | User search + role selector modal |
| Create | `frontend/src/pages/Domains/DomainPanel.tsx` | Side panel (desktop) + bottom sheet (mobile) |
| Create | `frontend/src/pages/Domains/index.tsx` | Full domains page |
| Modify | `frontend/src/pages/Profile.tsx` | Add admin section (PLATFORM_ADMIN only) |

---

## Task 1: Types + getDomainAccess helper

**Files:**
- Modify: `frontend/src/types/index.ts:68-71`
- Create: `frontend/src/lib/domains.ts`
- Create: `frontend/src/lib/domains.test.ts`

- [ ] **Step 1: Write failing test for getDomainAccess**

Create `frontend/src/lib/domains.test.ts`:

```typescript
import { describe, it, expect } from 'vitest'
import { getDomainAccess } from './domains'
import type { DomainWithMembers } from '../types'

const domain: DomainWithMembers = {
  id: '1',
  name: 'Analytics',
  description: 'Core analytics',
  owner_id: 'user-alice',
  owner_username: 'alice',
  members: [
    { user_id: 'user-bob', username: 'bob', role: 'maintainer' },
    { user_id: 'user-carol', username: 'carol', role: 'member' },
  ],
  contract_count: 2,
  created_at: '2024-01-01T00:00:00Z',
  updated_at: '2024-01-01T00:00:00Z',
}

describe('getDomainAccess', () => {
  it('returns "owner" for the domain owner', () => {
    expect(getDomainAccess(domain, 'user-alice')).toBe('owner')
  })

  it('returns "maintainer" for a maintainer member', () => {
    expect(getDomainAccess(domain, 'user-bob')).toBe('maintainer')
  })

  it('returns "member" for a regular member', () => {
    expect(getDomainAccess(domain, 'user-carol')).toBe('member')
  })

  it('returns "none" for a user not in the domain', () => {
    expect(getDomainAccess(domain, 'user-dave')).toBe('none')
  })

  it('owner check takes precedence even if owner is also listed as a member', () => {
    const d: DomainWithMembers = {
      ...domain,
      members: [
        ...domain.members,
        { user_id: 'user-alice', username: 'alice', role: 'member' },
      ],
    }
    expect(getDomainAccess(d, 'user-alice')).toBe('owner')
  })
})
```

- [ ] **Step 2: Run test — expect it to fail with "Cannot find module './domains'"**

```bash
cd frontend && npx vitest run --reporter=verbose src/lib/domains.test.ts
```

Expected: FAIL — `Error: Cannot find module './domains'`

- [ ] **Step 3: Update types/index.ts — replace Domain, add new types**

Replace lines 68–71 of `frontend/src/types/index.ts` (the existing minimal `Domain` interface) with:

```typescript
export interface Domain {
  id: string
  name: string
  description: string
  owner_id: string
  created_at: string
  updated_at: string
}

export interface DomainMember {
  user_id: string
  username: string
  role: 'maintainer' | 'member'
}

export interface DomainWithMembers extends Domain {
  owner_username: string
  members: DomainMember[]
  contract_count: number
}

export type DomainAccess = 'owner' | 'maintainer' | 'member' | 'none'

export interface DomainInput {
  name: string
  description: string
  owner_id: string
}
```

- [ ] **Step 4: Create frontend/src/lib/domains.ts**

```typescript
import type { DomainWithMembers, DomainAccess } from '../types'

export function getDomainAccess(domain: DomainWithMembers, userId: string): DomainAccess {
  if (domain.owner_id === userId) return 'owner'
  const member = domain.members.find((m) => m.user_id === userId)
  if (!member) return 'none'
  return member.role
}
```

- [ ] **Step 5: Run tests — expect all 5 to pass**

```bash
cd frontend && npx vitest run --reporter=verbose src/lib/domains.test.ts
```

Expected: PASS — 5 tests pass

- [ ] **Step 6: Commit**

```bash
cd frontend && git add src/types/index.ts src/lib/domains.ts src/lib/domains.test.ts
git commit -m "feat: add Domain types and getDomainAccess helper"
```

---

## Task 2: Domain CRUD hooks

**Files:**
- Create: `frontend/src/hooks/useDomains.ts`

- [ ] **Step 1: Create frontend/src/hooks/useDomains.ts**

```typescript
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { get, post, put, del } from '../lib/api'
import type { DomainWithMembers, DomainInput } from '../types'

const KEYS = {
  all: ['domains'] as const,
  one: (id: string) => ['domains', id] as const,
}

export function useAllDomains() {
  return useQuery<DomainWithMembers[]>({
    queryKey: KEYS.all,
    queryFn: () => get<DomainWithMembers[]>('/domains'),
  })
}

export function useCreateDomain() {
  const qc = useQueryClient()
  return useMutation<DomainWithMembers, Error, DomainInput>({
    mutationFn: (data) => post<DomainWithMembers>('/domains', data),
    onSuccess: () => qc.invalidateQueries({ queryKey: KEYS.all }),
  })
}

export function useUpdateDomain() {
  const qc = useQueryClient()
  return useMutation<DomainWithMembers, Error, { id: string } & Partial<DomainInput>>({
    mutationFn: ({ id, ...body }) => put<DomainWithMembers>(`/domains/${id}`, body),
    onSuccess: (updated) => {
      qc.invalidateQueries({ queryKey: KEYS.all })
      qc.invalidateQueries({ queryKey: KEYS.one(updated.id) })
    },
  })
}

export function useDeleteDomain() {
  const qc = useQueryClient()
  return useMutation<void, Error, string>({
    mutationFn: (id) => del(`/domains/${id}`),
    onSuccess: () => qc.invalidateQueries({ queryKey: KEYS.all }),
  })
}
```

- [ ] **Step 2: Verify TypeScript compiles without errors**

```bash
cd frontend && npx tsc --noEmit
```

Expected: no errors

- [ ] **Step 3: Commit**

```bash
cd frontend && git add src/hooks/useDomains.ts
git commit -m "feat: add domain CRUD hooks"
```

---

## Task 3: Domain member hooks

**Files:**
- Create: `frontend/src/hooks/useDomainMembers.ts`

- [ ] **Step 1: Create frontend/src/hooks/useDomainMembers.ts**

```typescript
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { post, patch, del } from '../lib/api'
import type { DomainMember } from '../types'

const KEYS = {
  all: ['domains'] as const,
}

export interface AddMemberInput {
  user_id: string
  role: 'maintainer' | 'member'
}

export function useAddDomainMember(domainId: string) {
  const qc = useQueryClient()
  return useMutation<DomainMember, Error, AddMemberInput>({
    mutationFn: (data) => post<DomainMember>(`/domains/${domainId}/members`, data),
    onSuccess: () => qc.invalidateQueries({ queryKey: KEYS.all }),
  })
}

export function useUpdateDomainMember(domainId: string) {
  const qc = useQueryClient()
  return useMutation<DomainMember, Error, { userId: string; role: 'maintainer' | 'member' }>({
    mutationFn: ({ userId, role }) =>
      patch<DomainMember>(`/domains/${domainId}/members/${userId}`, { role }),
    onSuccess: () => qc.invalidateQueries({ queryKey: KEYS.all }),
  })
}

export function useRemoveDomainMember(domainId: string) {
  const qc = useQueryClient()
  return useMutation<void, Error, string>({
    mutationFn: (userId) => del(`/domains/${domainId}/members/${userId}`),
    onSuccess: () => qc.invalidateQueries({ queryKey: KEYS.all }),
  })
}
```

- [ ] **Step 2: Verify TypeScript compiles**

```bash
cd frontend && npx tsc --noEmit
```

Expected: no errors

- [ ] **Step 3: Commit**

```bash
cd frontend && git add src/hooks/useDomainMembers.ts
git commit -m "feat: add domain member hooks"
```

---

## Task 4: Navigation + route

**Files:**
- Modify: `frontend/src/components/Sidebar.tsx:1-23`
- Modify: `frontend/src/components/BottomNav.tsx:1-9`
- Modify: `frontend/src/App.tsx`

- [ ] **Step 1: Update Sidebar.tsx — add Building2 import and Domains nav item**

Replace the import block and `navItems` array in `frontend/src/components/Sidebar.tsx` (lines 1–23):

```typescript
import { useState } from 'react'
import { NavLink, Link } from 'react-router-dom'
import {
  LayoutDashboard,
  FileText,
  Package,
  Users,
  Database,
  Sun,
  Moon,
  LogOut,
  Building2,
} from 'lucide-react'
import { useTheme } from '../contexts/ThemeContext'
import { useAuth } from '../contexts/AuthContext'
import { post } from '../lib/api'
import { getRefreshToken } from '../lib/auth'

const navItems = [
  { to: '/dashboard', icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/domains', icon: Building2, label: 'Domains' },
  { to: '/data-contracts', icon: FileText, label: 'Data Contracts' },
  { to: '/data-products', icon: Package, label: 'Data Products' },
  { to: '/users', icon: Users, label: 'Users' },
]
```

- [ ] **Step 2: Update BottomNav.tsx — add Building2 import and Domains nav item**

Replace the full content of `frontend/src/components/BottomNav.tsx`:

```typescript
import { NavLink } from 'react-router-dom'
import { LayoutDashboard, FileText, Package, Users, Building2 } from 'lucide-react'

const navItems = [
  { to: '/dashboard', icon: LayoutDashboard, label: 'Home' },
  { to: '/domains', icon: Building2, label: 'Domains' },
  { to: '/data-contracts', icon: FileText, label: 'Contracts' },
  { to: '/data-products', icon: Package, label: 'Products' },
  { to: '/users', icon: Users, label: 'Users' },
]

export default function BottomNav() {
  return (
    <nav aria-label="Mobile navigation" className="md:hidden fixed bottom-0 left-0 right-0 h-16 bg-slate-900 border-t border-slate-800 flex items-stretch z-50">
      {navItems.map(({ to, icon: Icon, label }) => (
        <NavLink
          key={to}
          to={to}
          className={({ isActive }) => `bottom-nav-link ${isActive ? 'active' : ''}`}
        >
          <Icon size={20} />
          <span>{label}</span>
        </NavLink>
      ))}
    </nav>
  )
}
```

- [ ] **Step 3: Add /domains route to App.tsx**

Add the import and route. Replace the import block at the top of `frontend/src/App.tsx`:

```typescript
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider } from './contexts/AuthContext'
import PrivateRoute from './components/PrivateRoute'
import Layout from './components/Layout'
import Login from './pages/Login'
import Dashboard from './pages/Dashboard'
import DomainsList from './pages/Domains'
import DataContractsList from './pages/DataContracts'
import DataContractDetail from './pages/DataContracts/DataContractDetail'
import NewDataContract from './pages/DataContracts/NewDataContract'
import DataProductsList from './pages/DataProducts'
import DataProductDetail from './pages/DataProducts/DataProductDetail'
import UsersList from './pages/Users'
import Profile from './pages/Profile'
```

Then add the route inside the `<Route path="/" element={<Layout />}>` block, after the `dashboard` route:

```tsx
<Route path="domains" element={<DomainsList />} />
```

- [ ] **Step 4: Verify TypeScript compiles (import of DomainsList will fail until Task 8, so skip type check until then)**

```bash
cd frontend && npx tsc --noEmit 2>&1 | head -20
```

Expected: error about `'./pages/Domains'` not found — this is expected, resolved in Task 8.

- [ ] **Step 5: Commit**

```bash
cd frontend && git add src/components/Sidebar.tsx src/components/BottomNav.tsx src/App.tsx
git commit -m "feat: add Domains to navigation and routing"
```

---

## Task 5: DomainCard component

**Files:**
- Create: `frontend/src/pages/Domains/DomainCard.tsx`
- Create: `frontend/src/pages/Domains/DomainCard.test.tsx`

- [ ] **Step 1: Write failing test**

Create `frontend/src/pages/Domains/DomainCard.test.tsx`:

```typescript
import { render, screen, fireEvent } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import DomainCard from './DomainCard'
import type { DomainWithMembers } from '../../types'

const domain: DomainWithMembers = {
  id: '1',
  name: 'Analytics',
  description: 'Core analytics domain',
  owner_id: 'user-alice',
  owner_username: 'alice',
  members: [{ user_id: 'user-bob', username: 'bob', role: 'member' }],
  contract_count: 3,
  created_at: '2024-01-01T00:00:00Z',
  updated_at: '2024-01-01T00:00:00Z',
}

describe('DomainCard', () => {
  it('renders the domain name', () => {
    render(<DomainCard domain={domain} access="member" isSelected={false} onClick={vi.fn()} />)
    expect(screen.getByText('Analytics')).toBeInTheDocument()
  })

  it('renders the description', () => {
    render(<DomainCard domain={domain} access="member" isSelected={false} onClick={vi.fn()} />)
    expect(screen.getByText('Core analytics domain')).toBeInTheDocument()
  })

  it('renders "Owner" badge when access is owner', () => {
    render(<DomainCard domain={domain} access="owner" isSelected={false} onClick={vi.fn()} />)
    expect(screen.getByText('Owner')).toBeInTheDocument()
    expect(screen.getByTestId('domain-card')).toHaveAttribute('data-access', 'owner')
  })

  it('renders "Maintainer" badge when access is maintainer', () => {
    render(<DomainCard domain={domain} access="maintainer" isSelected={false} onClick={vi.fn()} />)
    expect(screen.getByText('Maintainer')).toBeInTheDocument()
  })

  it('renders "Member" badge when access is member', () => {
    render(<DomainCard domain={domain} access="member" isSelected={false} onClick={vi.fn()} />)
    expect(screen.getByText('Member')).toBeInTheDocument()
  })

  it('renders "No Access" badge when access is none', () => {
    render(<DomainCard domain={domain} access="none" isSelected={false} onClick={vi.fn()} />)
    expect(screen.getByText('No Access')).toBeInTheDocument()
  })

  it('calls onClick when the card is clicked', () => {
    const handleClick = vi.fn()
    render(<DomainCard domain={domain} access="member" isSelected={false} onClick={handleClick} />)
    fireEvent.click(screen.getByTestId('domain-card'))
    expect(handleClick).toHaveBeenCalledOnce()
  })

  it('shows member count', () => {
    render(<DomainCard domain={domain} access="member" isSelected={false} onClick={vi.fn()} />)
    expect(screen.getByText(/1/)).toBeInTheDocument()
  })

  it('shows contract count', () => {
    render(<DomainCard domain={domain} access="member" isSelected={false} onClick={vi.fn()} />)
    expect(screen.getByText(/3/)).toBeInTheDocument()
  })
})
```

- [ ] **Step 2: Run test — expect it to fail with "Cannot find module './DomainCard'"**

```bash
cd frontend && npx vitest run --reporter=verbose src/pages/Domains/DomainCard.test.tsx
```

Expected: FAIL — `Error: Cannot find module './DomainCard'`

- [ ] **Step 3: Create frontend/src/pages/Domains/DomainCard.tsx**

```tsx
import Badge from '../../components/ui/Badge'
import type { DomainWithMembers, DomainAccess } from '../../types'

const ACCESS_CARD_CLASSES: Record<DomainAccess, string> = {
  owner:
    'border-[1.5px] border-indigo-500 bg-indigo-50 dark:bg-indigo-900/20 dark:border-indigo-400',
  maintainer:
    'border-[1.5px] border-amber-400 bg-amber-50 dark:bg-amber-900/20 dark:border-amber-400',
  member:
    'border-[1.5px] border-green-500 bg-green-50 dark:bg-green-900/20 dark:border-green-400',
  none: 'border border-slate-200 bg-slate-50 dark:bg-slate-800/50 dark:border-slate-700 opacity-65',
}

const ACCESS_BADGE_VARIANT: Record<DomainAccess, 'purple' | 'yellow' | 'green' | 'gray'> = {
  owner: 'purple',
  maintainer: 'yellow',
  member: 'green',
  none: 'gray',
}

const ACCESS_LABELS: Record<DomainAccess, string> = {
  owner: 'Owner',
  maintainer: 'Maintainer',
  member: 'Member',
  none: 'No Access',
}

interface DomainCardProps {
  domain: DomainWithMembers
  access: DomainAccess
  isSelected: boolean
  onClick: () => void
}

export default function DomainCard({ domain, access, isSelected, onClick }: DomainCardProps) {
  return (
    <button
      type="button"
      onClick={onClick}
      data-testid="domain-card"
      data-access={access}
      className={`w-full text-left rounded-xl p-3 transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-500 ring-offset-2 ${ACCESS_CARD_CLASSES[access]} ${isSelected ? 'ring-2 ring-indigo-400' : ''}`}
    >
      <div className="flex items-start justify-between gap-2 mb-1.5">
        <span className="font-semibold text-sm text-slate-900 dark:text-white truncate">
          {domain.name}
        </span>
        <Badge variant={ACCESS_BADGE_VARIANT[access]} className="shrink-0 text-[10px]">
          {ACCESS_LABELS[access]}
        </Badge>
      </div>
      <p className="text-xs text-slate-500 dark:text-slate-400 line-clamp-2 mb-2">
        {domain.description}
      </p>
      <div className="flex gap-3 text-[10px] text-slate-400">
        <span>👥 {domain.members.length}</span>
        <span>📄 {domain.contract_count}</span>
      </div>
    </button>
  )
}
```

- [ ] **Step 4: Run tests — expect all 9 to pass**

```bash
cd frontend && npx vitest run --reporter=verbose src/pages/Domains/DomainCard.test.tsx
```

Expected: PASS — 9 tests pass

- [ ] **Step 5: Commit**

```bash
cd frontend && git add src/pages/Domains/DomainCard.tsx src/pages/Domains/DomainCard.test.tsx
git commit -m "feat: add DomainCard component"
```

---

## Task 6: AddMemberModal component

**Files:**
- Create: `frontend/src/pages/Domains/AddMemberModal.tsx`

- [ ] **Step 1: Create frontend/src/pages/Domains/AddMemberModal.tsx**

```tsx
import { useState, useMemo } from 'react'
import { useUsers } from '../../hooks/useUsers'
import { useAddDomainMember } from '../../hooks/useDomainMembers'
import type { DomainWithMembers } from '../../types'
import Modal from '../../components/ui/Modal'
import Button from '../../components/ui/Button'
import { Input } from '../../components/ui/Input'

interface AddMemberModalProps {
  domain: DomainWithMembers
  open: boolean
  onClose: () => void
}

export default function AddMemberModal({ domain, open, onClose }: AddMemberModalProps) {
  const [search, setSearch] = useState('')
  const [selectedUserId, setSelectedUserId] = useState<string | null>(null)
  const [role, setRole] = useState<'member' | 'maintainer'>('member')

  const { data: users = [] } = useUsers()
  const addMember = useAddDomainMember(domain.id)

  const existingIds = useMemo(
    () => new Set([domain.owner_id, ...domain.members.map((m) => m.user_id)]),
    [domain],
  )

  const filtered = useMemo(
    () =>
      users.filter(
        (u) =>
          !existingIds.has(u.id) &&
          u.username.toLowerCase().includes(search.toLowerCase()),
      ),
    [users, existingIds, search],
  )

  function handleClose() {
    setSearch('')
    setSelectedUserId(null)
    setRole('member')
    onClose()
  }

  async function handleSubmit() {
    if (!selectedUserId) return
    try {
      await addMember.mutateAsync({ user_id: selectedUserId, role })
      handleClose()
    } catch {
      // error surfaced via addMember.error
    }
  }

  return (
    <Modal open={open} onClose={handleClose} title="Add Member" size="sm">
      <div className="space-y-4">
        <Input
          label="Search users"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Type a username…"
        />

        <div className="max-h-40 overflow-y-auto border border-slate-200 dark:border-slate-700 rounded-lg divide-y divide-slate-100 dark:divide-slate-700">
          {filtered.length === 0 ? (
            <p className="text-sm text-slate-500 text-center py-6">No users found.</p>
          ) : (
            filtered.map((u) => (
              <button
                key={u.id}
                type="button"
                onClick={() => setSelectedUserId(u.id)}
                className={`w-full text-left px-3 py-2.5 text-sm transition-colors ${
                  selectedUserId === u.id
                    ? 'bg-indigo-600 text-white'
                    : 'text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-700'
                }`}
              >
                {u.username}
              </button>
            ))
          )}
        </div>

        <div>
          <p className="text-xs font-medium text-slate-700 dark:text-slate-300 mb-1.5">Role</p>
          <div className="flex gap-2">
            {(['member', 'maintainer'] as const).map((r) => (
              <button
                key={r}
                type="button"
                onClick={() => setRole(r)}
                className={`flex-1 py-2 rounded-lg text-xs font-medium border transition-colors ${
                  role === r
                    ? 'bg-indigo-600 text-white border-indigo-600'
                    : 'border-slate-200 dark:border-slate-600 text-slate-600 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-700'
                }`}
              >
                {r.charAt(0).toUpperCase() + r.slice(1)}
              </button>
            ))}
          </div>
        </div>

        {addMember.error && (
          <p className="text-xs text-red-600 dark:text-red-400">
            {(addMember.error as Error).message}
          </p>
        )}

        <div className="flex gap-2 pt-1">
          <Button variant="secondary" onClick={handleClose} className="flex-1">
            Cancel
          </Button>
          <Button
            onClick={handleSubmit}
            disabled={!selectedUserId}
            loading={addMember.isPending}
            className="flex-1"
          >
            Add Member
          </Button>
        </div>
      </div>
    </Modal>
  )
}
```

- [ ] **Step 2: Verify TypeScript compiles**

```bash
cd frontend && npx tsc --noEmit 2>&1 | grep -v "pages/Domains/index"
```

Expected: no new errors (ignore missing `pages/Domains/index` until Task 8)

- [ ] **Step 3: Commit**

```bash
cd frontend && git add src/pages/Domains/AddMemberModal.tsx
git commit -m "feat: add AddMemberModal component"
```

---

## Task 7: DomainPanel component

**Files:**
- Create: `frontend/src/pages/Domains/DomainPanel.tsx`

- [ ] **Step 1: Create frontend/src/pages/Domains/DomainPanel.tsx**

```tsx
import { useState } from 'react'
import { X, UserPlus, Pencil } from 'lucide-react'
import { useRemoveDomainMember } from '../../hooks/useDomainMembers'
import { useUpdateDomain } from '../../hooks/useDomains'
import type { DomainWithMembers, DomainAccess } from '../../types'
import Badge from '../../components/ui/Badge'
import Button from '../../components/ui/Button'
import Modal from '../../components/ui/Modal'
import { Input } from '../../components/ui/Input'
import { Textarea } from '../../components/ui/Input'
import AddMemberModal from './AddMemberModal'

const MEMBER_ROLE_VARIANT = {
  maintainer: 'yellow',
  member: 'green',
} as const

interface DomainPanelProps {
  domain: DomainWithMembers
  access: DomainAccess
  onClose: () => void
}

function EditDomainModal({
  domain,
  open,
  onClose,
}: {
  domain: DomainWithMembers
  open: boolean
  onClose: () => void
}) {
  const [name, setName] = useState(domain.name)
  const [description, setDescription] = useState(domain.description)
  const update = useUpdateDomain()

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    try {
      await update.mutateAsync({ id: domain.id, name, description })
      onClose()
    } catch {
      // error surfaced via update.error
    }
  }

  return (
    <Modal open={open} onClose={onClose} title="Edit Domain" size="sm">
      <form onSubmit={handleSubmit} className="space-y-4">
        <Input
          label="Name"
          value={name}
          onChange={(e) => setName(e.target.value)}
          required
        />
        <Textarea
          label="Description"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          rows={3}
          required
        />
        {update.error && (
          <p className="text-xs text-red-600 dark:text-red-400">
            {(update.error as Error).message}
          </p>
        )}
        <div className="flex gap-2 pt-1">
          <Button variant="secondary" onClick={onClose} className="flex-1">
            Cancel
          </Button>
          <Button type="submit" loading={update.isPending} className="flex-1">
            Save
          </Button>
        </div>
      </form>
    </Modal>
  )
}

function PanelContent({
  domain,
  access,
  onClose,
}: DomainPanelProps) {
  const [addOpen, setAddOpen] = useState(false)
  const [editOpen, setEditOpen] = useState(false)
  const removeMember = useRemoveDomainMember(domain.id)

  const isOwner = access === 'owner'
  const canSeeMembers = access !== 'none'

  return (
    <div className="flex flex-col gap-4 h-full">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div className="min-w-0">
          <h2 className="font-bold text-base text-slate-900 dark:text-white truncate">
            {domain.name}
          </h2>
          <Badge
            variant={
              access === 'owner'
                ? 'purple'
                : access === 'maintainer'
                  ? 'yellow'
                  : access === 'member'
                    ? 'green'
                    : 'gray'
            }
            className="mt-1 text-[10px]"
          >
            {access === 'owner'
              ? 'Owner'
              : access === 'maintainer'
                ? 'Maintainer'
                : access === 'member'
                  ? 'Member'
                  : 'No Access'}
          </Badge>
        </div>
        <button
          type="button"
          onClick={onClose}
          className="p-1 rounded-lg text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-700 transition-colors shrink-0"
          aria-label="Close panel"
        >
          <X size={15} />
        </button>
      </div>

      {/* Description */}
      <p className="text-xs text-slate-500 dark:text-slate-400 leading-relaxed">
        {domain.description}
      </p>

      {/* Owner */}
      <div>
        <p className="text-[10px] font-semibold uppercase tracking-wider text-slate-400 mb-2">
          Owner
        </p>
        <div className="flex items-center gap-2">
          <div className="w-5 h-5 rounded-full bg-indigo-500 flex items-center justify-center shrink-0">
            <span className="text-white text-[9px] font-bold">
              {domain.owner_username.charAt(0).toUpperCase()}
            </span>
          </div>
          <span className="text-xs text-slate-700 dark:text-slate-300">
            {domain.owner_username}
          </span>
        </div>
      </div>

      {/* Members */}
      {canSeeMembers && (
        <div className="flex-1 min-h-0">
          <div className="flex items-center justify-between mb-2">
            <p className="text-[10px] font-semibold uppercase tracking-wider text-slate-400">
              Members ({domain.members.length})
            </p>
            {isOwner && (
              <button
                type="button"
                onClick={() => setAddOpen(true)}
                className="flex items-center gap-1 text-[10px] font-medium text-indigo-600 hover:text-indigo-700 dark:text-indigo-400"
              >
                <UserPlus size={11} />
                Add
              </button>
            )}
          </div>
          <div className="space-y-2 overflow-y-auto max-h-48">
            {domain.members.length === 0 ? (
              <p className="text-xs text-slate-400">No members yet.</p>
            ) : (
              domain.members.map((m) => (
                <div key={m.user_id} className="flex items-center justify-between gap-2">
                  <div className="flex items-center gap-2 min-w-0">
                    <div className="w-5 h-5 rounded-full bg-slate-400 flex items-center justify-center shrink-0">
                      <span className="text-white text-[9px] font-bold">
                        {m.username.charAt(0).toUpperCase()}
                      </span>
                    </div>
                    <span className="text-xs text-slate-700 dark:text-slate-300 truncate">
                      {m.username}
                    </span>
                  </div>
                  <div className="flex items-center gap-1.5 shrink-0">
                    <Badge variant={MEMBER_ROLE_VARIANT[m.role]} className="text-[9px]">
                      {m.role.charAt(0).toUpperCase() + m.role.slice(1)}
                    </Badge>
                    {isOwner && (
                      <button
                        type="button"
                        onClick={() => removeMember.mutate(m.user_id)}
                        className="text-slate-300 hover:text-red-500 dark:text-slate-600 dark:hover:text-red-400 transition-colors text-xs leading-none"
                        aria-label={`Remove ${m.username}`}
                      >
                        ✕
                      </button>
                    )}
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      )}

      {/* Owner: edit button */}
      {isOwner && (
        <div className="border-t border-slate-100 dark:border-slate-700 pt-3 mt-auto">
          <Button
            variant="secondary"
            size="sm"
            onClick={() => setEditOpen(true)}
            className="w-full flex items-center justify-center gap-1.5"
          >
            <Pencil size={12} />
            Edit Domain Info
          </Button>
        </div>
      )}

      <AddMemberModal domain={domain} open={addOpen} onClose={() => setAddOpen(false)} />
      <EditDomainModal domain={domain} open={editOpen} onClose={() => setEditOpen(false)} />
    </div>
  )
}

export default function DomainPanel(props: DomainPanelProps) {
  return (
    <>
      {/* Desktop: side panel */}
      <div className="hidden md:flex flex-col w-72 shrink-0 border-l border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 p-4 overflow-y-auto">
        <PanelContent {...props} />
      </div>

      {/* Mobile: bottom sheet overlay */}
      <div className="md:hidden fixed inset-0 z-40">
        <div
          className="absolute inset-0 bg-black/40"
          onClick={props.onClose}
          aria-hidden="true"
        />
        <div className="absolute bottom-0 left-0 right-0 bg-white dark:bg-slate-800 rounded-t-2xl max-h-[75vh] flex flex-col p-4 pb-8">
          <div className="w-8 h-1 bg-slate-300 dark:bg-slate-600 rounded-full mx-auto mb-4 shrink-0" />
          <div className="flex-1 overflow-y-auto">
            <PanelContent {...props} />
          </div>
        </div>
      </div>
    </>
  )
}
```

- [ ] **Step 2: Verify TypeScript compiles**

```bash
cd frontend && npx tsc --noEmit 2>&1 | grep -v "pages/Domains/index"
```

Expected: no errors (aside from missing index.tsx)

- [ ] **Step 3: Commit**

```bash
cd frontend && git add src/pages/Domains/DomainPanel.tsx
git commit -m "feat: add DomainPanel component (side panel + bottom sheet)"
```

---

## Task 8: Domains page

**Files:**
- Create: `frontend/src/pages/Domains/index.tsx`

- [ ] **Step 1: Create frontend/src/pages/Domains/index.tsx**

```tsx
import { useState, useMemo } from 'react'
import { Building2 } from 'lucide-react'
import { useAllDomains } from '../../hooks/useDomains'
import { useAuth } from '../../contexts/AuthContext'
import { getDomainAccess } from '../../lib/domains'
import type { DomainWithMembers, DomainAccess } from '../../types'
import DomainCard from './DomainCard'
import DomainPanel from './DomainPanel'

type FilterTab = 'all' | DomainAccess

const FILTER_LABELS: Record<FilterTab, string> = {
  all: 'All',
  owner: 'Owner',
  maintainer: 'Maintainer',
  member: 'Member',
  none: 'No Access',
}

export default function DomainsList() {
  const { user } = useAuth()
  const { data: domains = [], isLoading, error } = useAllDomains()
  const [filter, setFilter] = useState<FilterTab>('all')
  const [selectedId, setSelectedId] = useState<string | null>(null)

  const domainsWithAccess = useMemo(
    () =>
      domains.map((d) => ({
        domain: d,
        access: user ? getDomainAccess(d, user.id) : ('none' as DomainAccess),
      })),
    [domains, user],
  )

  const counts = useMemo(
    () =>
      domainsWithAccess.reduce(
        (acc, { access }) => {
          acc[access] = (acc[access] ?? 0) + 1
          return acc
        },
        {} as Record<DomainAccess, number>,
      ),
    [domainsWithAccess],
  )

  const filtered = useMemo(
    () =>
      filter === 'all'
        ? domainsWithAccess
        : domainsWithAccess.filter(({ access }) => access === filter),
    [domainsWithAccess, filter],
  )

  const selectedEntry = domainsWithAccess.find(({ domain }) => domain.id === selectedId)

  const FILTER_TABS: { id: FilterTab; label: string; count: number }[] = [
    { id: 'all', label: 'All', count: domains.length },
    { id: 'owner', label: 'Owner', count: counts.owner ?? 0 },
    { id: 'maintainer', label: 'Maintainer', count: counts.maintainer ?? 0 },
    { id: 'member', label: 'Member', count: counts.member ?? 0 },
  ]

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-48 text-slate-500 dark:text-slate-400 text-sm">
        Loading domains…
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center h-48 gap-3">
        <p className="text-sm text-red-600 dark:text-red-400">
          Failed to load domains. {(error as Error).message}
        </p>
        <button
          type="button"
          onClick={() => window.location.reload()}
          className="text-xs text-indigo-600 underline"
        >
          Retry
        </button>
      </div>
    )
  }

  return (
    <div className="flex flex-col h-full">
      {/* Page header */}
      <div className="flex items-center gap-3 px-1 mb-4">
        <Building2 size={20} className="text-slate-500 dark:text-slate-400 shrink-0" />
        <div>
          <h1 className="text-xl font-semibold text-slate-900 dark:text-white">Domains</h1>
          <p className="text-xs text-slate-500 dark:text-slate-400">
            Browse all domains and manage your access
          </p>
        </div>
      </div>

      {/* Filter chips (mobile) / tabs (desktop) */}
      <div className="mb-4">
        {/* Mobile: scrollable pill chips */}
        <div className="flex gap-2 overflow-x-auto pb-1 md:hidden">
          {FILTER_TABS.filter((t) => t.count > 0 || t.id === 'all').map((tab) => (
            <button
              key={tab.id}
              type="button"
              onClick={() => { setFilter(tab.id); setSelectedId(null) }}
              className={`shrink-0 px-3 py-1.5 rounded-full text-xs font-medium transition-colors ${
                filter === tab.id
                  ? 'bg-indigo-600 text-white'
                  : 'bg-slate-100 dark:bg-slate-700 text-slate-600 dark:text-slate-300'
              }`}
            >
              {tab.label} ({tab.count})
            </button>
          ))}
        </div>

        {/* Desktop: underline tabs */}
        <div className="hidden md:flex border-b border-slate-200 dark:border-slate-700 gap-1">
          {FILTER_TABS.filter((t) => t.count > 0 || t.id === 'all').map((tab) => (
            <button
              key={tab.id}
              type="button"
              onClick={() => { setFilter(tab.id); setSelectedId(null) }}
              className={`px-4 py-2 text-sm font-medium transition-colors ${
                filter === tab.id
                  ? 'text-indigo-600 dark:text-indigo-400 border-b-2 border-indigo-600 dark:border-indigo-400'
                  : 'text-slate-500 dark:text-slate-400 hover:text-slate-700 dark:hover:text-slate-200'
              }`}
            >
              {tab.label} ({tab.count})
            </button>
          ))}
        </div>
      </div>

      {/* Content area */}
      <div className="flex flex-1 min-h-0 gap-0">
        {/* Card grid */}
        <div className="flex-1 overflow-y-auto">
          {filtered.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-48 gap-2 text-slate-400">
              <Building2 size={32} className="opacity-30" />
              <p className="text-sm">
                {filter === 'all' ? 'No domains exist yet.' : `No domains with "${FILTER_LABELS[filter]}" access.`}
              </p>
            </div>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
              {filtered.map(({ domain, access }) => (
                <DomainCard
                  key={domain.id}
                  domain={domain}
                  access={access}
                  isSelected={domain.id === selectedId}
                  onClick={() =>
                    setSelectedId((prev) => (prev === domain.id ? null : domain.id))
                  }
                />
              ))}
            </div>
          )}
        </div>

        {/* DomainPanel renders once. Desktop: `hidden md:flex` side panel participates
            in flex layout as a sibling. Mobile: `md:hidden fixed` bottom sheet uses
            fixed positioning so DOM location doesn't matter — renders as overlay. */}
        {selectedEntry && (
          <DomainPanel
            domain={selectedEntry.domain}
            access={selectedEntry.access}
            onClose={() => setSelectedId(null)}
          />
        )}
      </div>
    </div>
  )
}

- [ ] **Step 2: Verify TypeScript compiles with no errors**

```bash
cd frontend && npx tsc --noEmit
```

Expected: no errors

- [ ] **Step 3: Run full test suite to confirm nothing broke**

```bash
cd frontend && npx vitest run --reporter=verbose
```

Expected: all existing tests pass

- [ ] **Step 4: Commit**

```bash
cd frontend && git add src/pages/Domains/index.tsx
git commit -m "feat: add Domains page with filter tabs and panel"
```

---

## Task 9: Profile admin section

**Files:**
- Modify: `frontend/src/pages/Profile.tsx`

- [ ] **Step 1: Add imports to Profile.tsx**

Add these imports to the top of `frontend/src/pages/Profile.tsx`, after the existing imports:

```typescript
import { Textarea } from '../components/ui/Input'
import Modal from '../components/ui/Modal'
import Table from '../components/ui/Table'
import { useAllDomains, useCreateDomain, useUpdateDomain, useDeleteDomain } from '../hooks/useDomains'
import { useUsers } from '../hooks/useUsers'
import type { DomainWithMembers, DomainInput } from '../types'
```

Also add `ShieldAlert` and `Trash2` to the existing lucide-react import:

```typescript
import {
  Shield,
  ShieldAlert,
  Building2,
  User as UserIcon,
  Lock,
  ChevronRight,
  Eye,
  EyeOff,
  CheckCircle2,
  XCircle,
  Trash2,
  Pencil,
  Plus,
} from 'lucide-react'
```

- [ ] **Step 2: Extend Section type and NAV array**

Replace lines 65–70 in `frontend/src/pages/Profile.tsx` (the `Section` type and `NAV` const) with:

```typescript
type Section = 'role' | 'password' | 'admin-domains' | 'admin-users'

const ACCOUNT_NAV: { id: Section; label: string; icon: React.ReactNode }[] = [
  { id: 'role', label: 'My Role', icon: <Shield size={16} /> },
  { id: 'password', label: 'Change Password', icon: <Lock size={16} /> },
]

const ADMIN_NAV: { id: Section; label: string; icon: React.ReactNode }[] = [
  { id: 'admin-domains', label: 'Domains', icon: <Building2 size={16} /> },
  { id: 'admin-users', label: 'Users', icon: <ShieldAlert size={16} /> },
]
```

- [ ] **Step 3: Add AdminDomainsSection component (inline in Profile.tsx, before the Profile export)**

Add after the `PasswordSection` function and before the `// ── Page ──` comment:

```tsx
// ── Admin sections ───────────────────────────────────────────────────────────

function DomainFormModal({
  domain,
  open,
  onClose,
}: {
  domain: DomainWithMembers | null
  open: boolean
  onClose: () => void
}) {
  const { data: users = [] } = useUsers()
  const createDomain = useCreateDomain()
  const updateDomain = useUpdateDomain()

  const [name, setName] = useState(domain?.name ?? '')
  const [description, setDescription] = useState(domain?.description ?? '')
  const [ownerId, setOwnerId] = useState(domain?.owner_id ?? '')
  const [ownerSearch, setOwnerSearch] = useState(domain?.owner_username ?? '')

  const mutation = domain ? updateDomain : createDomain

  const filteredUsers = users.filter((u) =>
    u.username.toLowerCase().includes(ownerSearch.toLowerCase()),
  )

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    const data: DomainInput = { name, description, owner_id: ownerId }
    try {
      if (domain) {
        await updateDomain.mutateAsync({ id: domain.id, ...data })
      } else {
        await createDomain.mutateAsync(data)
      }
      onClose()
    } catch {
      // error surfaced via mutation.error
    }
  }

  return (
    <Modal
      open={open}
      onClose={onClose}
      title={domain ? 'Edit Domain' : 'New Domain'}
      size="sm"
    >
      <form onSubmit={handleSubmit} className="space-y-4">
        <Input
          label="Name"
          value={name}
          onChange={(e) => setName(e.target.value)}
          required
        />
        <Textarea
          label="Description"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          rows={3}
          required
        />
        <div>
          <Input
            label="Owner"
            value={ownerSearch}
            onChange={(e) => {
              setOwnerSearch(e.target.value)
              setOwnerId('')
            }}
            placeholder="Search by username…"
          />
          {ownerSearch && !ownerId && filteredUsers.length > 0 && (
            <div className="mt-1 border border-slate-200 dark:border-slate-700 rounded-lg overflow-hidden max-h-32 overflow-y-auto">
              {filteredUsers.map((u) => (
                <button
                  key={u.id}
                  type="button"
                  onClick={() => {
                    setOwnerId(u.id)
                    setOwnerSearch(u.username)
                  }}
                  className="w-full text-left px-3 py-2 text-sm hover:bg-slate-50 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-300"
                >
                  {u.username}
                </button>
              ))}
            </div>
          )}
          {!ownerId && ownerSearch && filteredUsers.length === 0 && (
            <p className="text-xs text-slate-400 mt-1">No users found.</p>
          )}
        </div>

        {mutation.error && (
          <p className="text-xs text-red-600 dark:text-red-400">
            {(mutation.error as Error).message}
          </p>
        )}

        <div className="flex gap-2 pt-1">
          <Button variant="secondary" onClick={onClose} className="flex-1">
            Cancel
          </Button>
          <Button
            type="submit"
            loading={mutation.isPending}
            disabled={!name || !description || !ownerId}
            className="flex-1"
          >
            {domain ? 'Save' : 'Create'}
          </Button>
        </div>
      </form>
    </Modal>
  )
}

function DeleteDomainModal({
  domain,
  open,
  onClose,
}: {
  domain: DomainWithMembers | null
  open: boolean
  onClose: () => void
}) {
  const deleteDomain = useDeleteDomain()

  async function handleDelete() {
    if (!domain) return
    try {
      await deleteDomain.mutateAsync(domain.id)
      onClose()
    } catch {
      // error surfaced via deleteDomain.error
    }
  }

  return (
    <Modal open={open} onClose={onClose} title="Delete Domain" size="sm">
      <div className="space-y-4">
        <p className="text-sm text-slate-700 dark:text-slate-300">
          Delete <strong>{domain?.name}</strong>? This will not delete associated data contracts.
          All members will lose domain access.
        </p>
        {deleteDomain.error && (
          <p className="text-xs text-red-600 dark:text-red-400">
            {(deleteDomain.error as Error).message}
          </p>
        )}
        <div className="flex gap-2">
          <Button variant="secondary" onClick={onClose} className="flex-1">
            Cancel
          </Button>
          <Button
            variant="danger"
            loading={deleteDomain.isPending}
            onClick={handleDelete}
            className="flex-1"
          >
            Delete
          </Button>
        </div>
      </div>
    </Modal>
  )
}

function AdminDomainsSection() {
  const { data: domains = [], isLoading } = useAllDomains()
  const [formOpen, setFormOpen] = useState(false)
  const [editTarget, setEditTarget] = useState<DomainWithMembers | null>(null)
  const [deleteTarget, setDeleteTarget] = useState<DomainWithMembers | null>(null)

  const columns = [
    {
      key: 'name',
      header: 'Name',
      render: (d: DomainWithMembers) => (
        <span className="font-medium text-slate-900 dark:text-white">{d.name}</span>
      ),
    },
    {
      key: 'owner',
      header: 'Owner',
      render: (d: DomainWithMembers) => (
        <span className="text-slate-500 dark:text-slate-400">{d.owner_username}</span>
      ),
    },
    {
      key: 'members',
      header: 'Members',
      render: (d: DomainWithMembers) => (
        <span className="text-slate-500 dark:text-slate-400">{d.members.length}</span>
      ),
    },
    {
      key: 'contracts',
      header: 'Contracts',
      render: (d: DomainWithMembers) => (
        <span className="text-slate-500 dark:text-slate-400">{d.contract_count}</span>
      ),
    },
    {
      key: 'actions',
      header: '',
      render: (d: DomainWithMembers) => (
        <div className="flex gap-2 justify-end">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => { setEditTarget(d); setFormOpen(true) }}
            className="flex items-center gap-1"
          >
            <Pencil size={12} /> Edit
          </Button>
          <Button
            variant="danger"
            size="sm"
            onClick={() => setDeleteTarget(d)}
            className="flex items-center gap-1"
          >
            <Trash2 size={12} /> Delete
          </Button>
        </div>
      ),
    },
  ]

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="font-semibold text-slate-900 dark:text-white">Manage Domains</h2>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
            Create, edit, and delete platform domains
          </p>
        </div>
        <Button
          size="sm"
          variant="danger"
          onClick={() => { setEditTarget(null); setFormOpen(true) }}
          className="flex items-center gap-1.5"
        >
          <Plus size={13} /> New Domain
        </Button>
      </div>

      {isLoading ? (
        <p className="text-sm text-slate-500 dark:text-slate-400">Loading…</p>
      ) : (
        <Table
          columns={columns}
          data={domains}
          keyExtractor={(d) => d.id}
          emptyMessage="No domains yet."
        />
      )}

      <DomainFormModal
        domain={editTarget}
        open={formOpen}
        onClose={() => { setFormOpen(false); setEditTarget(null) }}
      />
      <DeleteDomainModal
        domain={deleteTarget}
        open={!!deleteTarget}
        onClose={() => setDeleteTarget(null)}
      />
    </div>
  )
}

function AdminUsersSection() {
  return (
    <div className="card p-6 text-center">
      <ShieldAlert size={32} className="mx-auto text-slate-300 dark:text-slate-600 mb-3" />
      <p className="text-sm font-medium text-slate-700 dark:text-slate-300">
        User management coming soon.
      </p>
      <p className="text-xs text-slate-400 mt-1">
        Additional admin functions will be added here.
      </p>
    </div>
  )
}
```

- [ ] **Step 4: Update the Profile component to wire up admin nav**

Replace the `Profile` export function in `frontend/src/pages/Profile.tsx`. The key changes are:
1. `section` state default stays `'role'`
2. Nav renders two groups: Account and Admin (admin only visible to PLATFORM_ADMIN)
3. Admin section content renders for `admin-domains` and `admin-users`

Replace the entire `export default function Profile()` block with:

```tsx
export default function Profile() {
  const { user } = useAuth()
  const [section, setSection] = useState<Section>('role')
  const isAdmin = user?.role === 'PLATFORM_ADMIN'

  if (!user) return null

  const role = ROLE_META[user.role] ?? {
    label: user.role,
    color: 'bg-slate-100 text-slate-700 dark:bg-slate-700/50 dark:text-slate-300',
    description: '',
    permissions: [],
  }

  const allNavItems = [
    ...ACCOUNT_NAV,
    ...(isAdmin ? ADMIN_NAV : []),
  ]

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <h1 className="text-xl font-semibold text-slate-900 dark:text-white">My Profile</h1>

      {/* Identity card — always visible */}
      <div className="card p-6 flex items-center gap-5">
        <div className="w-14 h-14 rounded-full bg-indigo-600 flex items-center justify-center shrink-0">
          <span className="text-white text-2xl font-bold">
            {user.username.charAt(0).toUpperCase()}
          </span>
        </div>
        <div className="min-w-0">
          <p className="text-lg font-semibold text-slate-900 dark:text-white truncate">
            {user.username}
          </p>
          <p className="text-sm text-slate-500 dark:text-slate-400 truncate">{user.email}</p>
          <span className={`mt-1.5 inline-block px-2.5 py-0.5 rounded-full text-xs font-semibold ${role.color}`}>
            {role.label}
          </span>
        </div>
      </div>

      {/* Two-column: sidebar nav + content */}
      <div className="flex flex-col md:flex-row gap-4">

        {/* Sidebar nav */}
        <nav className="md:w-48 shrink-0">
          {/* Mobile: horizontal scrollable tab row */}
          <div className="flex md:hidden gap-1 card p-1 overflow-x-auto">
            {ACCOUNT_NAV.map((item) => (
              <button
                key={item.id}
                onClick={() => setSection(item.id)}
                className={`shrink-0 flex flex-col items-center gap-1 py-2 px-2 rounded-md text-xs font-medium transition-colors ${
                  section === item.id
                    ? 'bg-indigo-600 text-white'
                    : 'text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-700'
                }`}
              >
                {item.icon}
                <span className="leading-none">{item.label.split(' ')[0]}</span>
              </button>
            ))}
            {isAdmin &&
              ADMIN_NAV.map((item) => (
                <button
                  key={item.id}
                  onClick={() => setSection(item.id)}
                  className={`shrink-0 flex flex-col items-center gap-1 py-2 px-2 rounded-md text-xs font-medium transition-colors ${
                    section === item.id
                      ? 'bg-red-600 text-white'
                      : 'text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20'
                  }`}
                >
                  {item.icon}
                  <span className="leading-none">🛡 {item.label}</span>
                </button>
              ))}
          </div>

          {/* Desktop: vertical list with sections */}
          <div className="hidden md:flex flex-col card p-2 gap-0.5">
            <p className="px-3 py-1 text-[10px] font-semibold uppercase tracking-wider text-slate-400">
              Account
            </p>
            {ACCOUNT_NAV.map((item) => (
              <button
                key={item.id}
                onClick={() => setSection(item.id)}
                className={`flex items-center gap-2.5 px-3 py-2.5 rounded-md text-sm font-medium transition-colors w-full text-left ${
                  section === item.id
                    ? 'bg-indigo-600 text-white'
                    : 'text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-700'
                }`}
              >
                {item.icon}
                {item.label}
              </button>
            ))}
            {isAdmin && (
              <>
                <p className="px-3 py-1 mt-2 text-[10px] font-semibold uppercase tracking-wider text-red-500">
                  🛡 Admin
                </p>
                {ADMIN_NAV.map((item) => (
                  <button
                    key={item.id}
                    onClick={() => setSection(item.id)}
                    className={`flex items-center gap-2.5 px-3 py-2.5 rounded-md text-sm font-medium transition-colors w-full text-left ${
                      section === item.id
                        ? 'bg-red-600 text-white'
                        : 'text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20'
                    }`}
                  >
                    {item.icon}
                    {item.label}
                  </button>
                ))}
              </>
            )}
          </div>
        </nav>

        {/* Content panel */}
        <div className="flex-1 min-w-0">
          {section === 'role' && <RoleSection userId={user.id} />}
          {section === 'password' && <PasswordSection userId={user.id} />}
          {section === 'admin-domains' && isAdmin && <AdminDomainsSection />}
          {section === 'admin-users' && isAdmin && <AdminUsersSection />}
        </div>
      </div>
    </div>
  )
}
```

- [ ] **Step 5: Verify TypeScript compiles clean**

```bash
cd frontend && npx tsc --noEmit
```

Expected: no errors

- [ ] **Step 6: Run full test suite**

```bash
cd frontend && npx vitest run --reporter=verbose
```

Expected: all tests pass

- [ ] **Step 7: Commit**

```bash
cd frontend && git add src/pages/Profile.tsx
git commit -m "feat: add admin panel to Profile page (Domains + Users stub)"
```

---

## Self-review checklist

After all tasks:

- [ ] **Run full test suite one final time**

```bash
cd frontend && npx vitest run
```

Expected: all tests pass, coverage above 80% thresholds

- [ ] **Run TypeScript check**

```bash
cd frontend && npx tsc --noEmit
```

Expected: no errors

- [ ] **Final commit if any cleanup needed**

```bash
git add -p  # stage any remaining changes
git commit -m "chore: final cleanup for domains feature"
```
