# Responsive Design

**Date:** 2026-04-23
**Branch:** feature/login-frontpage
**Status:** Approved

## Problem

The app is not usable on mobile or low-resolution screens. The sidebar is a fixed 256px column that never shrinks or hides, content pages have no responsive padding, and data tables overflow horizontally without any fallback.

## Decisions

| Question | Decision |
|---|---|
| Mobile navigation pattern | Bottom navigation bar (sidebar hidden, bottom bar with icon + label for each route) |
| Table on mobile | Card stack — each row becomes a card with label/value pairs |
| Breakpoint | Tailwind `md` (768px) — below this is "mobile", at and above is "desktop" |
| Implementation approach | Tailwind-native responsive prefixes; no new libraries |

## Architecture

No new pages or routes. Changes span one new component and modifications to seven existing files.

**New file:**
- `frontend/src/components/BottomNav.tsx` — mobile-only navigation bar

**Modified files:**
- `frontend/src/components/Layout.tsx` — hide sidebar on mobile, add bottom padding for bottom nav
- `frontend/src/components/Sidebar.tsx` — `hidden md:flex` so it vanishes below 768px
- `frontend/src/components/ui/Table.tsx` — responsive card stack mode via optional `mobileCardConfig` prop
- `frontend/src/pages/Login.tsx` — ensure card is full-width with safe edge padding on small screens
- `frontend/src/pages/DataContracts/index.tsx` — pass `mobileCardConfig` to Table
- `frontend/src/pages/DataProducts/index.tsx` — pass `mobileCardConfig` to Table
- `frontend/src/pages/Users/index.tsx` — pass `mobileCardConfig` to Table
- `frontend/src/index.css` — add `.bottom-nav-link` component class

## Components

### BottomNav.tsx

Renders only on mobile (`md:hidden`). Fixed to the bottom of the viewport. Contains the same 4 nav items as the Sidebar (Dashboard, Data Contracts, Data Products, Users) using `NavLink` with active state styling.

Layout: full-width `fixed bottom-0`, dark slate background matching the sidebar (`bg-slate-900`), top border (`border-slate-800`), 4 items spaced evenly with `justify-around`. Each item: icon (16px from lucide-react) + label below it (10px). Active item highlights in blue (`text-blue-400`), inactive in slate (`text-slate-400`).

Height: `h-16` (64px). This drives the bottom padding added to Layout.

### Table.tsx — mobileCardConfig prop

New optional prop:

```ts
mobileCardConfig?: {
  titleKey: string       // column key to use as the card heading
  badgeKey?: string      // column key to render as a badge in the top-right corner
}
```

When `mobileCardConfig` is provided, the component renders two sibling divs:
1. `<div className="hidden md:block">` — existing table markup unchanged
2. `<div className="md:hidden space-y-3">` — card list

Each card:
- Dark card background matching the table body (`bg-white dark:bg-slate-800`), rounded-xl, border
- Top row: title (from `titleKey` column's `render`) on the left, badge column (from `badgeKey`) on the right if specified
- Remaining columns rendered as a 2-column grid of label/value pairs below the title row
- Labels use the column's `header` string in uppercase, `text-xs text-gray-400 dark:text-slate-500`
- Values use the column's `render` function unchanged (so badges, links, etc. carry over)
- `onRowClick` still works — cards get the same click handler

When `mobileCardConfig` is absent, the component renders exactly as today (no behaviour change for existing usages).

### Layout.tsx

```tsx
// Before
<div className="flex min-h-screen bg-gray-50 dark:bg-slate-900">
  <Sidebar />
  <main className="flex-1 overflow-y-auto ...">
    <div className="p-8"><Outlet /></div>
  </main>
</div>

// After
<div className="flex min-h-screen bg-gray-50 dark:bg-slate-900">
  <Sidebar />
  <main className="flex-1 overflow-y-auto ...">
    <div className="p-4 md:p-8 pb-20 md:pb-8"><Outlet /></div>
  </main>
  <BottomNav />
</div>
```

`pb-20` on mobile ensures content is never hidden behind the 64px bottom nav.

### Sidebar.tsx

Add `hidden md:flex` to the `<aside>` element. No other changes. The sidebar continues to work identically on desktop.

### Login.tsx

The card container currently has inline styles that set a fixed width. Ensure the card uses `w-full` with a `max-w-sm` cap and `mx-4` horizontal margin so it never touches screen edges on narrow viewports. The dark background gradient already fills the full viewport so no changes needed there.

## Breakpoints

Single breakpoint throughout: Tailwind `md` (768px).

- `< 768px`: bottom nav visible, sidebar hidden, content padding `p-4`, table card mode active
- `≥ 768px`: sidebar visible, bottom nav hidden, content padding `p-8`, table mode as today

## Error Handling

No new error states. The bottom nav and card layouts use the same data and auth flow as the existing components.

## Testing

Manual smoke tests after implementation:
1. Resize browser to 375px width — sidebar must disappear, bottom nav must appear
2. Navigate between all 4 routes via the bottom nav — active state highlights correctly
3. Open Data Contracts, Data Products, Users at 375px — rows render as cards, not overflow
4. Click a card row — row click handler fires correctly (navigates to detail)
5. Open Login at 375px — card does not overflow or clip
6. Resize back to 1024px — sidebar appears, bottom nav disappears, tables revert to normal
7. Dark mode toggle still works from the sidebar footer on desktop
