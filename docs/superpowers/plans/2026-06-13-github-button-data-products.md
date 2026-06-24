# GitHub Button on Data Products Pages — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a GitHub icon link to the data products list and detail pages that opens the provisioned repo in a new tab when `repo_url` is available.

**Architecture:** The backend already returns `repo_url` in `DataProductResponseModel`; only frontend changes are needed. The type is updated first, then each page adds a conditional `<a>` tag (not a `<button>`) styled to match the existing button system.

**Tech Stack:** React 18, TypeScript, Tailwind CSS, lucide-react, Vitest, @testing-library/react, react-router-dom v6

---

## Files

| Action | Path |
|--------|------|
| Modify | `frontend/src/types/index.ts` |
| Modify | `frontend/src/pages/DataProducts/DataProductDetail.tsx` |
| Create | `frontend/src/pages/DataProducts/DataProductDetail.test.tsx` |
| Modify | `frontend/src/pages/DataProducts/index.tsx` |
| Create | `frontend/src/pages/DataProducts/DataProductsList.test.tsx` |

---

## Task 1: Add `repo_url` to the `DataProduct` frontend type

**Files:**
- Modify: `frontend/src/types/index.ts`

- [ ] **Step 1: Add the field to the interface**

In `frontend/src/types/index.ts`, locate the `DataProduct` interface (currently lines 53–60) and add `repo_url`:

```ts
export interface DataProduct {
  id: string
  name: string
  description: string
  data_contracts_id: string
  repo_url?: string | null   // provisioned GitHub repo URL; null until backend provisions it
  created_at: string
  updated_at: string
}
```

- [ ] **Step 2: Verify TypeScript compiles cleanly**

```bash
cd frontend && npx tsc --noEmit
```

Expected: no errors. (The field is optional so existing code that constructs `DataProduct` objects without `repo_url` stays valid.)

- [ ] **Step 3: Commit**

```bash
git add frontend/src/types/index.ts
git commit -m "feat: add repo_url to DataProduct frontend type"
```

---

## Task 2: GitHub button on the detail page (TDD)

**Files:**
- Create: `frontend/src/pages/DataProducts/DataProductDetail.test.tsx`
- Modify: `frontend/src/pages/DataProducts/DataProductDetail.tsx`

### Step 1 — Write the failing tests

- [ ] **Create `frontend/src/pages/DataProducts/DataProductDetail.test.tsx`**

```tsx
import { render, screen } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import DataProductDetail from './DataProductDetail'
import {
  useDataProduct,
  useUpdateDataProduct,
  useDeleteDataProduct,
} from '../../hooks/useDataProducts'

vi.mock('../../hooks/useDataProducts', () => ({
  useDataProduct: vi.fn(),
  useUpdateDataProduct: vi.fn(),
  useDeleteDataProduct: vi.fn(),
}))

const baseProduct = {
  id: 'prod-123',
  name: 'My Product',
  description: 'A test product',
  data_contracts_id: 'contract-abc',
  repo_url: null,
  created_at: '2024-01-01T00:00:00Z',
  updated_at: '2024-01-01T00:00:00Z',
}

function renderDetail() {
  return render(
    <MemoryRouter initialEntries={['/data-products/prod-123']}>
      <Routes>
        <Route path="/data-products/:id" element={<DataProductDetail />} />
      </Routes>
    </MemoryRouter>
  )
}

describe('DataProductDetail — GitHub button', () => {
  beforeEach(() => {
    vi.mocked(useUpdateDataProduct).mockReturnValue({
      mutateAsync: vi.fn(),
      isPending: false,
      isError: false,
      error: null,
    } as any)
    vi.mocked(useDeleteDataProduct).mockReturnValue({
      mutateAsync: vi.fn(),
      isPending: false,
      isError: false,
      error: null,
    } as any)
  })

  it('renders a GitHub link when repo_url is a non-empty string', () => {
    vi.mocked(useDataProduct).mockReturnValue({
      data: { ...baseProduct, repo_url: 'https://github.com/org/dp-test' },
      isLoading: false,
      error: null,
    } as any)

    renderDetail()

    const link = screen.getByRole('link', { name: /github/i })
    expect(link).toHaveAttribute('href', 'https://github.com/org/dp-test')
    expect(link).toHaveAttribute('target', '_blank')
    expect(link).toHaveAttribute('rel', 'noopener noreferrer')
  })

  it('does not render a GitHub link when repo_url is null', () => {
    vi.mocked(useDataProduct).mockReturnValue({
      data: { ...baseProduct, repo_url: null },
      isLoading: false,
      error: null,
    } as any)

    renderDetail()

    expect(screen.queryByRole('link', { name: /github/i })).not.toBeInTheDocument()
  })

  it('does not render a GitHub link when repo_url is undefined', () => {
    vi.mocked(useDataProduct).mockReturnValue({
      data: { ...baseProduct },
      isLoading: false,
      error: null,
    } as any)

    renderDetail()

    expect(screen.queryByRole('link', { name: /github/i })).not.toBeInTheDocument()
  })
})
```

- [ ] **Step 2: Run tests — expect FAIL**

```bash
cd frontend && npm test -- DataProductDetail
```

Expected output: `FAIL` — `getByRole('link', { name: /github/i })` finds nothing because the link doesn't exist yet.

### Step 3 — Implement

- [ ] **Step 3: Update `frontend/src/pages/DataProducts/DataProductDetail.tsx`**

Add `Github` to the lucide-react import (line 3):

```tsx
import { Edit2, Trash2, Calendar, Clock, FileText, Github } from 'lucide-react'
```

In the `actions` prop of `<PageHeader>` (currently lines 80–98), prepend the GitHub link before the Edit button:

```tsx
actions={
  <>
    {product.repo_url && (
      <a
        href={product.repo_url}
        target="_blank"
        rel="noopener noreferrer"
        className="btn-secondary text-xs px-3 py-1.5"
      >
        <Github size={14} />
        GitHub
      </a>
    )}
    <Button
      variant="secondary"
      size="sm"
      onClick={() => setEditOpen(true)}
    >
      <Edit2 size={14} />
      Edit
    </Button>
    <Button
      variant="danger"
      size="sm"
      onClick={() => setDeleteConfirm(true)}
    >
      <Trash2 size={14} />
      Delete
    </Button>
  </>
}
```

- [ ] **Step 4: Run tests — expect PASS**

```bash
cd frontend && npm test -- DataProductDetail
```

Expected: all 3 tests pass.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/pages/DataProducts/DataProductDetail.test.tsx \
        frontend/src/pages/DataProducts/DataProductDetail.tsx
git commit -m "feat: add GitHub button to data product detail page"
```

---

## Task 3: GitHub icon link in the list page (TDD)

**Files:**
- Create: `frontend/src/pages/DataProducts/DataProductsList.test.tsx`
- Modify: `frontend/src/pages/DataProducts/index.tsx`

### Step 1 — Write the failing tests

- [ ] **Create `frontend/src/pages/DataProducts/DataProductsList.test.tsx`**

```tsx
import { render, screen, fireEvent } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { MemoryRouter } from 'react-router-dom'
import DataProductsList from './index'
import {
  useDataProducts,
  useCreateDataProduct,
  useDeleteDataProduct,
} from '../../hooks/useDataProducts'

const mockNavigate = vi.fn()

vi.mock('react-router-dom', async (importOriginal) => {
  const mod = await importOriginal<typeof import('react-router-dom')>()
  return { ...mod, useNavigate: () => mockNavigate }
})

vi.mock('../../hooks/useDataProducts', () => ({
  useDataProducts: vi.fn(),
  useCreateDataProduct: vi.fn(),
  useDeleteDataProduct: vi.fn(),
}))

const productWithRepo = {
  id: 'prod-1',
  name: 'Product With Repo',
  description: 'Has a GitHub repo',
  data_contracts_id: 'contract-1',
  repo_url: 'https://github.com/org/dp-test',
  created_at: '2024-01-01T00:00:00Z',
  updated_at: '2024-01-01T00:00:00Z',
}

const productWithoutRepo = {
  id: 'prod-2',
  name: 'Product Without Repo',
  description: 'No GitHub repo yet',
  data_contracts_id: 'contract-2',
  repo_url: null,
  created_at: '2024-01-01T00:00:00Z',
  updated_at: '2024-01-01T00:00:00Z',
}

function renderList() {
  return render(
    <MemoryRouter>
      <DataProductsList />
    </MemoryRouter>
  )
}

describe('DataProductsList — GitHub button', () => {
  beforeEach(() => {
    mockNavigate.mockClear()
    vi.mocked(useCreateDataProduct).mockReturnValue({
      mutateAsync: vi.fn(),
      isPending: false,
      isError: false,
      error: null,
    } as any)
    vi.mocked(useDeleteDataProduct).mockReturnValue({
      mutateAsync: vi.fn(),
      isPending: false,
      isError: false,
      error: null,
    } as any)
  })

  it('renders a GitHub link for a row that has repo_url', () => {
    vi.mocked(useDataProducts).mockReturnValue({
      data: [productWithRepo],
      isLoading: false,
      error: null,
    } as any)

    renderList()

    const link = screen.getByTitle('Open GitHub repo')
    expect(link).toHaveAttribute('href', 'https://github.com/org/dp-test')
    expect(link).toHaveAttribute('target', '_blank')
    expect(link).toHaveAttribute('rel', 'noopener noreferrer')
  })

  it('does not render a GitHub link for a row without repo_url', () => {
    vi.mocked(useDataProducts).mockReturnValue({
      data: [productWithoutRepo],
      isLoading: false,
      error: null,
    } as any)

    renderList()

    expect(screen.queryByTitle('Open GitHub repo')).not.toBeInTheDocument()
  })

  it('renders GitHub links only for rows that have repo_url when the list is mixed', () => {
    vi.mocked(useDataProducts).mockReturnValue({
      data: [productWithRepo, productWithoutRepo],
      isLoading: false,
      error: null,
    } as any)

    renderList()

    expect(screen.getAllByTitle('Open GitHub repo')).toHaveLength(1)
  })

  it('clicking the GitHub link does not trigger row navigation', () => {
    vi.mocked(useDataProducts).mockReturnValue({
      data: [productWithRepo],
      isLoading: false,
      error: null,
    } as any)

    renderList()

    fireEvent.click(screen.getByTitle('Open GitHub repo'))

    expect(mockNavigate).not.toHaveBeenCalledWith(`/data-products/${productWithRepo.id}`)
  })
})
```

- [ ] **Step 2: Run tests — expect FAIL**

```bash
cd frontend && npm test -- DataProductsList
```

Expected output: `FAIL` — `getByTitle('Open GitHub repo')` finds nothing.

### Step 3 — Implement

- [ ] **Step 3: Update `frontend/src/pages/DataProducts/index.tsx`**

Add `Github` to the lucide-react import (line 3):

```tsx
import { Plus, Package, Trash2, Github } from 'lucide-react'
```

Replace the `actions` column definition (currently the last entry in the `columns` array, around lines 85–101) with:

```tsx
{
  key: 'actions',
  header: '',
  render: (row: DataProduct) => (
    <div className="flex items-center gap-2">
      {row.repo_url && (
        <a
          href={row.repo_url}
          target="_blank"
          rel="noopener noreferrer"
          onClick={(e) => e.stopPropagation()}
          className="inline-flex items-center justify-center p-1.5 rounded text-gray-500 hover:text-gray-800 hover:bg-gray-100 dark:text-slate-400 dark:hover:text-slate-100 dark:hover:bg-slate-700 transition-colors"
          title="Open GitHub repo"
        >
          <Github size={13} />
        </a>
      )}
      <button
        onClick={(e) => {
          e.stopPropagation()
          setDeleteTarget(row)
        }}
        className="btn-danger"
        title="Delete"
      >
        <Trash2 size={13} />
        Delete
      </button>
    </div>
  ),
  className: 'w-32',
},
```

- [ ] **Step 4: Run tests — expect PASS**

```bash
cd frontend && npm test -- DataProductsList
```

Expected: all 4 tests pass.

- [ ] **Step 5: Run the full test suite to check for regressions**

```bash
cd frontend && npm test
```

Expected: all existing tests continue to pass.

- [ ] **Step 6: Commit**

```bash
git add frontend/src/pages/DataProducts/DataProductsList.test.tsx \
        frontend/src/pages/DataProducts/index.tsx
git commit -m "feat: add GitHub icon link to data products list page"
```
