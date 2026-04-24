# Responsive Design Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the Data Mesh Platform app fully usable on mobile and low-resolution screens using a bottom navigation bar pattern and card-stack tables.

**Architecture:** Tailwind responsive prefixes throughout, single `md` breakpoint (768px). New `BottomNav.tsx` replaces the sidebar on mobile. `Table.tsx` gets an optional `mobileCardConfig` prop that enables a card-stack view below `md`. No new dependencies.

**Tech Stack:** React 18, TypeScript, Tailwind CSS 3, Vite, React Router 6, Lucide React (icons), Vitest + @testing-library/react

---

### Task 1: BottomNav component + index.css class

**Files:**
- Create: `frontend/src/components/BottomNav.tsx`
- Modify: `frontend/src/index.css`

- [ ] **Step 1: Add the `.bottom-nav-link` component class to index.css**

In `frontend/src/index.css`, inside the `@layer components { ... }` block, add after `.sidebar-link.active`:

```css
  .bottom-nav-link {
    @apply flex flex-col items-center justify-center gap-1 flex-1 py-2 text-slate-400 hover:text-white transition-colors text-xs;
  }

  .bottom-nav-link.active {
    @apply text-blue-400;
  }
```

- [ ] **Step 2: Create BottomNav.tsx**

```tsx
import { NavLink } from 'react-router-dom'
import { LayoutDashboard, FileText, Package, Users } from 'lucide-react'

const navItems = [
  { to: '/dashboard', icon: LayoutDashboard, label: 'Home' },
  { to: '/data-contracts', icon: FileText, label: 'Contracts' },
  { to: '/data-products', icon: Package, label: 'Products' },
  { to: '/users', icon: Users, label: 'Users' },
]

export default function BottomNav() {
  return (
    <nav className="md:hidden fixed bottom-0 left-0 right-0 h-16 bg-slate-900 border-t border-slate-800 flex items-stretch z-50">
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

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/BottomNav.tsx frontend/src/index.css
git commit -m "feat: add BottomNav component and bottom-nav-link CSS class"
```

---

### Task 2: Layout + Sidebar responsive wiring

**Files:**
- Modify: `frontend/src/components/Sidebar.tsx:43`
- Modify: `frontend/src/components/Layout.tsx`

- [ ] **Step 1: Hide Sidebar on mobile**

In `frontend/src/components/Sidebar.tsx`, change the `<aside>` opening tag on line 43 from:

```tsx
    <aside className="w-64 shrink-0 bg-slate-900 min-h-screen flex flex-col">
```

to:

```tsx
    <aside className="hidden md:flex w-64 shrink-0 bg-slate-900 min-h-screen flex-col">
```

Note: `flex flex-col` becomes `md:flex flex-col` — `flex` is replaced by `md:flex` and `flex-col` stays so the column direction applies when the flex kicks in.

- [ ] **Step 2: Add BottomNav and responsive padding to Layout**

Replace the entire content of `frontend/src/components/Layout.tsx` with:

```tsx
import { Outlet } from 'react-router-dom'
import Sidebar from './Sidebar'
import BottomNav from './BottomNav'

export default function Layout() {
  return (
    <div className="flex min-h-screen bg-gray-50 dark:bg-slate-900">
      <Sidebar />
      <main className="flex-1 overflow-y-auto bg-gray-50 dark:bg-slate-900">
        <div className="p-4 md:p-8 pb-20 md:pb-8">
          <Outlet />
        </div>
      </main>
      <BottomNav />
    </div>
  )
}
```

`pb-20` (80px) on mobile ensures content is never hidden behind the 64px bottom nav. `md:pb-8` restores normal padding on desktop.

- [ ] **Step 3: Verify in browser**

Run the dev server:
```bash
cd frontend && npm run dev
```

Open http://localhost:5173. Resize the browser window below 768px — the sidebar should disappear and the bottom nav should appear fixed at the bottom. Resize above 768px — sidebar returns, bottom nav disappears.

- [ ] **Step 4: Commit**

```bash
git add frontend/src/components/Sidebar.tsx frontend/src/components/Layout.tsx
git commit -m "feat: hide sidebar and show bottom nav on mobile"
```

---

### Task 3: Table responsive card mode

**Files:**
- Modify: `frontend/src/components/ui/Table.tsx`
- Create: `frontend/src/components/ui/Table.test.tsx`

- [ ] **Step 1: Write the failing tests**

Create `frontend/src/components/ui/Table.test.tsx`:

```tsx
import { render, screen } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import Table from './Table'

const columns = [
  { key: 'name', header: 'Name', render: (row: { name: string }) => <span>{row.name}</span> },
  { key: 'email', header: 'Email', render: (row: { email: string }) => <span>{row.email}</span> },
  { key: 'actions', header: '', render: () => <button>Delete</button> },
]

const data = [
  { name: 'Alice', email: 'alice@example.com' },
  { name: 'Bob', email: 'bob@example.com' },
]

describe('Table', () => {
  it('renders a table when mobileCardConfig is not provided', () => {
    render(
      <Table
        columns={columns}
        data={data}
        keyExtractor={(r) => r.name}
      />
    )
    expect(screen.getByRole('table')).toBeInTheDocument()
  })

  it('renders mobile cards when mobileCardConfig is provided', () => {
    render(
      <Table
        columns={columns}
        data={data}
        keyExtractor={(r) => r.name}
        mobileCardConfig={{ titleKey: 'name' }}
      />
    )
    // Both table (desktop) and cards (mobile) are in the DOM — CSS hides one
    expect(screen.getByRole('table')).toBeInTheDocument()
    // Card titles appear
    expect(screen.getAllByText('Alice')).toHaveLength(2) // once in table, once in card
    expect(screen.getAllByText('Bob')).toHaveLength(2)
  })

  it('fires onRowClick when a card is clicked', async () => {
    const handleClick = vi.fn()
    render(
      <Table
        columns={columns}
        data={data}
        keyExtractor={(r) => r.name}
        onRowClick={handleClick}
        mobileCardConfig={{ titleKey: 'name' }}
      />
    )
    const cards = document.querySelectorAll('[data-testid="mobile-card"]')
    ;(cards[0] as HTMLElement).click()
    expect(handleClick).toHaveBeenCalledWith(data[0])
  })
})
```

- [ ] **Step 2: Run tests — expect failures**

```bash
cd frontend && npx vitest run src/components/ui/Table.test.tsx
```

Expected: 2–3 tests fail because `mobileCardConfig` prop doesn't exist and `data-testid="mobile-card"` isn't rendered.

- [ ] **Step 3: Implement mobileCardConfig in Table.tsx**

Replace `frontend/src/components/ui/Table.tsx` entirely with:

```tsx
import { ReactNode } from 'react'

interface Column<T> {
  key: string
  header: string
  render: (row: T) => ReactNode
  className?: string
}

interface MobileCardConfig {
  titleKey: string
  badgeKey?: string
}

interface TableProps<T> {
  columns: Column<T>[]
  data: T[]
  onRowClick?: (row: T) => void
  keyExtractor: (row: T) => string
  emptyMessage?: string
  mobileCardConfig?: MobileCardConfig
}

export default function Table<T>({
  columns,
  data,
  onRowClick,
  keyExtractor,
  emptyMessage = 'No records found.',
  mobileCardConfig,
}: TableProps<T>) {
  const tableNode = (
    <div className="overflow-x-auto rounded-xl border border-gray-200 dark:border-slate-700">
      <table className="min-w-full divide-y divide-gray-100 dark:divide-slate-700">
        <thead>
          <tr className="bg-gray-50 dark:bg-slate-700/50">
            {columns.map((col) => (
              <th
                key={col.key}
                scope="col"
                className={`px-4 py-3 text-left text-xs font-semibold text-gray-500 dark:text-slate-400 uppercase tracking-wider ${col.className ?? ''}`}
              >
                {col.header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="bg-white dark:bg-slate-800 divide-y divide-gray-100 dark:divide-slate-700">
          {data.length === 0 ? (
            <tr>
              <td
                colSpan={columns.length}
                className="px-4 py-12 text-center text-sm text-gray-400 dark:text-slate-500"
              >
                {emptyMessage}
              </td>
            </tr>
          ) : (
            data.map((row) => (
              <tr
                key={keyExtractor(row)}
                onClick={onRowClick ? () => onRowClick(row) : undefined}
                className={`transition-colors ${
                  onRowClick
                    ? 'cursor-pointer hover:bg-blue-50 dark:hover:bg-blue-900/20'
                    : 'hover:bg-gray-50 dark:hover:bg-slate-700'
                }`}
              >
                {columns.map((col) => (
                  <td
                    key={col.key}
                    className={`px-4 py-3 text-sm text-gray-700 dark:text-slate-300 ${col.className ?? ''}`}
                  >
                    {col.render(row)}
                  </td>
                ))}
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  )

  if (!mobileCardConfig) return tableNode

  const titleCol = columns.find((c) => c.key === mobileCardConfig.titleKey)
  const badgeCol = mobileCardConfig.badgeKey
    ? columns.find((c) => c.key === mobileCardConfig.badgeKey)
    : undefined
  const bodyColumns = columns.filter(
    (c) =>
      c.key !== mobileCardConfig.titleKey &&
      c.key !== mobileCardConfig.badgeKey &&
      c.header !== '',
  )
  const actionColumns = columns.filter(
    (c) => c.header === '' && c.key !== mobileCardConfig.badgeKey,
  )

  const cardListNode = (
    <div className="md:hidden space-y-3">
      {data.length === 0 ? (
        <p className="py-12 text-center text-sm text-gray-400 dark:text-slate-500">
          {emptyMessage}
        </p>
      ) : (
        data.map((row) => (
          <div
            key={keyExtractor(row)}
            data-testid="mobile-card"
            onClick={onRowClick ? () => onRowClick(row) : undefined}
            className={`bg-white dark:bg-slate-800 border border-gray-200 dark:border-slate-700 rounded-xl p-4 transition-colors ${
              onRowClick
                ? 'cursor-pointer hover:bg-blue-50 dark:hover:bg-blue-900/20'
                : ''
            }`}
          >
            <div className="flex items-start justify-between gap-2 mb-3">
              <div className="font-medium text-gray-900 dark:text-slate-100 min-w-0">
                {titleCol?.render(row)}
              </div>
              {badgeCol && <div className="shrink-0">{badgeCol.render(row)}</div>}
            </div>
            {bodyColumns.length > 0 && (
              <div className="grid grid-cols-2 gap-x-4 gap-y-3">
                {bodyColumns.map((col) => (
                  <div key={col.key}>
                    <div className="text-xs font-semibold text-gray-400 dark:text-slate-500 uppercase tracking-wider mb-0.5">
                      {col.header}
                    </div>
                    <div className="text-sm text-gray-700 dark:text-slate-300">
                      {col.render(row)}
                    </div>
                  </div>
                ))}
              </div>
            )}
            {actionColumns.map((col) => (
              <div
                key={col.key}
                className="mt-3 pt-3 border-t border-gray-100 dark:border-slate-700 flex justify-end"
              >
                {col.render(row)}
              </div>
            ))}
          </div>
        ))
      )}
    </div>
  )

  return (
    <>
      <div className="hidden md:block">{tableNode}</div>
      {cardListNode}
    </>
  )
}
```

- [ ] **Step 4: Run tests — expect all to pass**

```bash
cd frontend && npx vitest run src/components/ui/Table.test.tsx
```

Expected output:
```
✓ src/components/ui/Table.test.tsx (3)
  ✓ Table > renders a table when mobileCardConfig is not provided
  ✓ Table > renders mobile cards when mobileCardConfig is provided
  ✓ Table > fires onRowClick when a card is clicked
```

- [ ] **Step 5: Commit**

```bash
git add frontend/src/components/ui/Table.tsx frontend/src/components/ui/Table.test.tsx
git commit -m "feat: add responsive card stack mode to Table component"
```

---

### Task 4: Wire mobileCardConfig in data listing pages

**Files:**
- Modify: `frontend/src/pages/DataContracts/index.tsx:141-148`
- Modify: `frontend/src/pages/DataProducts/index.tsx:138-145`
- Modify: `frontend/src/pages/Users/index.tsx:172-178`

#### 4a — DataContracts

- [ ] **Step 1: Add mobileCardConfig to the DataContracts Table**

In `frontend/src/pages/DataContracts/index.tsx`, find the `<Table` call (around line 141) and add the `mobileCardConfig` prop:

```tsx
        <Table
          columns={columns}
          data={contracts}
          keyExtractor={(c) => c.id}
          onRowClick={(c) => navigate(`/data-contracts/${c.id}`)}
          emptyMessage="No contracts found."
          mobileCardConfig={{ titleKey: 'preview' }}
        />
```

`titleKey: 'preview'` uses the contract preview column as the card heading. The `created_at` column becomes the body field. The `actions` column (empty header, `key: 'actions'`) renders as the footer of each card.

- [ ] **Step 2: Commit**

```bash
git add frontend/src/pages/DataContracts/index.tsx
git commit -m "feat: enable responsive card view for Data Contracts table"
```

#### 4b — DataProducts

- [ ] **Step 3: Add mobileCardConfig to the DataProducts Table**

In `frontend/src/pages/DataProducts/index.tsx`, find the `<Table` call (around line 138) and add:

```tsx
        <Table
          columns={columns}
          data={products}
          keyExtractor={(p) => p.id}
          onRowClick={(p) => navigate(`/data-products/${p.id}`)}
          emptyMessage="No products found."
          mobileCardConfig={{ titleKey: 'name' }}
        />
```

`titleKey: 'name'` uses the product name as the card heading. The `description`, `contract`, and `created_at` columns form the body grid. The `actions` column renders as the card footer.

- [ ] **Step 4: Commit**

```bash
git add frontend/src/pages/DataProducts/index.tsx
git commit -m "feat: enable responsive card view for Data Products table"
```

#### 4c — Users

- [ ] **Step 5: Add mobileCardConfig to the Users Table**

In `frontend/src/pages/Users/index.tsx`, find the `<Table` call (around line 172) and add:

```tsx
        <Table
          columns={columns}
          data={users}
          keyExtractor={(u) => u.id}
          emptyMessage="No users found."
          mobileCardConfig={{ titleKey: 'name' }}
        />
```

`titleKey: 'name'` uses the avatar+username column as the card heading. The `email` and `id` columns form the body grid. The `actions` column (edit + delete buttons) renders as the card footer.

- [ ] **Step 6: Commit**

```bash
git add frontend/src/pages/Users/index.tsx
git commit -m "feat: enable responsive card view for Users table"
```

---

### Task 5: Login page mobile padding fix

**Files:**
- Modify: `frontend/src/pages/Login.tsx:251-261`

- [ ] **Step 1: Move padding from inline style to className**

In `frontend/src/pages/Login.tsx`, find the glass card `<div>` around line 251. It currently has `padding: '40px 36px'` inside the inline `style` object. Remove the `padding` from the inline style and add responsive padding classes to `className`.

Change:

```tsx
      {/* Glass card */}
      <div
        className="relative z-10 w-full mx-4"
        style={{
          maxWidth: '400px',
          background: 'rgba(255,255,255,0.05)',
          backdropFilter: 'blur(20px)',
          WebkitBackdropFilter: 'blur(20px)',
          border: '1px solid rgba(255,255,255,0.1)',
          borderRadius: '20px',
          padding: '40px 36px',
        }}
      >
```

To:

```tsx
      {/* Glass card */}
      <div
        className="relative z-10 w-full mx-4 p-5 sm:px-9 sm:py-10"
        style={{
          maxWidth: '400px',
          background: 'rgba(255,255,255,0.05)',
          backdropFilter: 'blur(20px)',
          WebkitBackdropFilter: 'blur(20px)',
          border: '1px solid rgba(255,255,255,0.1)',
          borderRadius: '20px',
        }}
      >
```

`p-5` = 20px all sides on small screens. `sm:px-9` = 36px horizontal and `sm:py-10` = 40px vertical on ≥ 640px (matches the original 40px/36px values exactly).

- [ ] **Step 2: Verify in browser at 375px width**

With the dev server running, open http://localhost:5173/login in Chrome DevTools mobile mode (375px). The card should fill the screen width minus 32px (2×mx-4=2×16px) and the form fields should be comfortably spaced. No horizontal overflow.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/pages/Login.tsx
git commit -m "fix: use responsive padding on login card for small screens"
```

---

### Task 6: Manual smoke tests

Run the dev server (`cd frontend && npm run dev`) and open http://localhost:5173. Open Chrome DevTools → toggle device toolbar → set to iPhone 12 Pro (390×844).

- [ ] Sidebar is not visible at 390px
- [ ] Bottom nav bar is fixed at the bottom with 4 items: Home, Contracts, Products, Users
- [ ] Tapping each bottom nav item navigates to the correct route
- [ ] Active nav item is highlighted in blue
- [ ] Content does not overlap the bottom nav (scroll to bottom of a list)
- [ ] Data Contracts page at 390px shows cards, not a table
- [ ] Data Products page at 390px shows cards, not a table
- [ ] Users page at 390px shows cards, not a table
- [ ] Clicking a card row navigates to the detail page (Data Contracts, Data Products)
- [ ] Delete button on a card triggers the delete confirmation modal
- [ ] Login page at 390px — card fits the screen with no horizontal scroll
- [ ] Set device to 1280px wide — sidebar appears, bottom nav gone, tables are back
- [ ] Dark mode toggle in sidebar footer still works on desktop
- [ ] Run the full test suite: `cd frontend && npx vitest run` — all tests pass

- [ ] **Final commit** (if any tweaks were needed during smoke tests)

```bash
git add -p  # stage only the tweaks
git commit -m "fix: responsive smoke test tweaks"
```
