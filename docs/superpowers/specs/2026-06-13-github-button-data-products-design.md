# GitHub Button on Data Products Pages — Design Spec

**Date:** 2026-06-13

## Summary

Add a GitHub icon button to the data products UI that opens the provisioned GitHub repository for a product in a new browser tab. The button appears on both the list page (per row) and the detail page (header actions bar). It renders only when the product has a `repo_url`.

## Context

The backend already provisions a GitHub repo for each data product and stores its URL in the `repo_url` column. The `DataProductResponseModel` already returns `repo_url: str | None`. The frontend `DataProduct` type does not yet expose this field, so the URL is currently silently dropped.

## Scope

Three files change; no new files are created:

1. `frontend/src/types/index.ts` — add `repo_url` to the `DataProduct` interface
2. `frontend/src/pages/DataProducts/DataProductDetail.tsx` — add GitHub button to header actions
3. `frontend/src/pages/DataProducts/index.tsx` — add GitHub icon button to table row actions column

## Design Decisions

### Link element, not a button

Use a native `<a href={repo_url} target="_blank" rel="noopener noreferrer">` styled with Tailwind to match the `secondary` button appearance. This is semantically correct for external navigation and preserves right-click / cmd+click behavior. The existing `Button` component is not extended.

### Conditional rendering

The button renders only when `repo_url` is a non-empty string. When `repo_url` is `null` or `undefined` (GitHub not configured, or provisioning hasn't run yet), the element is absent — no disabled state, no placeholder.

### Icon

Use `Github` from `lucide-react`, consistent with all other icons in the project.

### Click isolation on the list page

The list table has row-click navigation (`onRowClick`). The GitHub link in the actions column must call `e.stopPropagation()` to prevent the row click from also navigating to the detail page (following the same pattern as the existing Delete button).

## Detail Page

In `DataProductDetail.tsx`, the `PageHeader` `actions` prop currently renders `<Edit>` and `<Delete>` buttons. When `product.repo_url` is set, a GitHub link is prepended to that group:

```tsx
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
```

## List Page

In the `columns` array in `index.tsx`, the `actions` column currently renders a Delete button. A GitHub icon link is added alongside it when the row has a `repo_url`:

```tsx
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
```

## Type Change

```ts
export interface DataProduct {
  id: string
  name: string
  description: string
  data_contracts_id: string
  repo_url?: string | null   // added
  created_at: string
  updated_at: string
}
```

## Out of Scope

- No backend changes (field already returned)
- No changes to `DataProductFormData` (repo_url is read-only, set by the server)
- No badge/status indicator for "repo pending" state
- No tooltip showing the full URL on hover
