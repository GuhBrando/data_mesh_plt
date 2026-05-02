# GitHub Code Quality Validation — Design Spec

**Date:** 2026-04-30  
**Branch:** feature/code-quality-improvement  
**Status:** Approved

---

## Overview

Add two new GitHub Actions workflows (`quality.yml`, `security.yml`) to enforce code quality and security gates on the Data Mesh Platform. All checks are blocking — PRs cannot merge unless every check passes. The existing `ci.yml` (ruff lint + pytest) is untouched.

---

## Workflow Structure

```
.github/workflows/
  ci.yml          ← existing, untouched
  quality.yml     ← new: coverage, complexity, mutation, N+1, static race/leak
  security.yml    ← new: secret scan, security lint, dependency audit
```

### Triggers

**`quality.yml`**
- `push` to any branch: fast jobs only (coverage, complexity, N+1, static analysis) — ~2–4 min
- `pull_request` to `main` or `develop`: fast jobs + mutation tests — ~10–20 min total

**`security.yml`**
- `push` to any branch: gitleaks secret scan only (~30s)
- `pull_request` to `main` or `develop`: all security checks
- `schedule` weekly (Monday 08:00 UTC): dependency scan only (catches new CVEs against pinned deps)

---

## Job Dependency Graph

### `quality.yml`
```
[coverage-python]  ──┐
[coverage-react]   ──┤
[complexity]       ──┼──► [mutation-python]  (PR only, depends on coverage-python)
[n1-detector]      ──┤
[static-analysis]  ──┘    [mutation-react]   (PR only, depends on coverage-react)
```
Fast jobs run in parallel. Mutation jobs wait for coverage to pass first.

### `security.yml`
```
[secret-scan] ──► [security-lint-python]
              └──► [security-lint-react]
              └──► [dependency-audit]
```
Secret scan runs first. All other jobs depend on it (no point scanning code if secrets are already exposed).

---

## Tool Configuration

### Python Backend

| Check | Tool | Config |
|---|---|---|
| Coverage | `pytest-cov` | `--cov=backend --cov-fail-under=80 --cov-report=xml` |
| Cyclomatic Complexity | `ruff` (C90) — blocking; `radon` — informational report | ruff max-complexity = 15 (blocks merge); radon CC report uploaded as artifact |
| N+1 Detection | Custom pytest fixture | Wraps asyncpg pool, counts queries per request; fails if list endpoint issues N+1 queries |
| Static Race/Leak | `ruff` ASYNC + SIM rules | Catches unawaited coroutines, async-unsafe stdlib calls, common resource leak patterns |
| Mutation | `mutmut` | `--paths-to-mutate=backend/ --runner="pytest tests/" --threshold=70` |
| Security Lint | `bandit` | `-r backend/ -ll` (medium+ severity blocking) |
| Dependency Scan | `pip-audit` | fail on high/critical CVEs |

### React Frontend

| Check | Tool | Config |
|---|---|---|
| Coverage | `vitest --coverage` (v8) | thresholds: lines 80%, functions 80%, branches 80%, statements 80% |
| Cyclomatic Complexity | ESLint `complexity` rule | `["error", 15]` — same threshold as backend |
| N+1 Detection | `@tanstack/eslint-plugin-query` | Detects unstable query keys (causing refetches), missing dependencies, patterns that lead to N+1 fetches |
| Static Race/Leak | `eslint-plugin-react-hooks` | `exhaustive-deps`, `rules-of-hooks` |
| Leak Runtime | `vitest` global setup | `afterEach` spy on `console.error` — fails if "state update on unmounted component" warning fires |
| Mutation | `stryker` + `@stryker-mutator/vitest-runner` | `mutate: ["src/**/*.tsx", "src/**/*.ts"]`, `thresholds: { break: 70 }` |
| Security Lint | `eslint-plugin-security` | `detect-non-literal-regexp`, `detect-object-injection`, `detect-possible-timing-attacks` |
| Dependency Scan | `npm audit` | `--audit-level=high` |

### Secret Scan

| Check | Tool | Config |
|---|---|---|
| Secret Scan | `gitleaks-action` v2 | Scans full git history on PRs; blocks all downstream jobs if secrets found |

---

## Project Config Changes

### `pyproject.toml`

Add to `[project.optional-dependencies] dev`:
```toml
"pytest-cov>=5.0.0",
"radon>=6.0.0",
"mutmut>=2.4.0",
"bandit>=1.7.0",
"pip-audit>=2.7.0",
```

Add to `[tool.ruff.lint] select`:
```toml
"C90",   # McCabe complexity
"ASYNC", # async safety rules
```

Add new section:
```toml
[tool.ruff.lint.mccabe]
max-complexity = 15
```

### `frontend/vite.config.ts`

Add `test.coverage` block:
```ts
test: {
  coverage: {
    provider: "v8",
    thresholds: { lines: 80, functions: 80, branches: 80, statements: 80 },
    reporter: ["text", "lcov"],
  },
  setupFiles: ["./src/test/setup.ts"],
}
```

### `frontend/eslint.config.js`

Add plugins and rules:
```js
// plugins: eslint-plugin-security, @tanstack/eslint-plugin-query, eslint-plugin-react-hooks
rules: {
  "complexity": ["error", 15],
  "react-hooks/rules-of-hooks": "error",
  "react-hooks/exhaustive-deps": "warn",
  "security/detect-non-literal-regexp": "error",
  "security/detect-object-injection": "warn",  // TypeScript typed access produces false positives at error level
  "security/detect-possible-timing-attacks": "error",
}
```

### `frontend/package.json` — new devDependencies

```json
"@stryker-mutator/core": "^8.0.0",
"@stryker-mutator/vitest-runner": "^8.0.0",
"@vitest/coverage-v8": "^4.0.0",
"eslint-plugin-security": "^3.0.0",
"@tanstack/eslint-plugin-query": "^5.0.0"
```

### New Files

| File | Purpose |
|---|---|
| `stryker.config.mjs` | Stryker mutation config for React/TS |
| `frontend/src/test/setup.ts` | Global vitest setup: leak spy + afterEach cleanup |
| `tests/conftest.py` (additions) | asyncpg query-counting fixture for N+1 detection |

---

## Thresholds Summary

| Metric | Threshold | Behavior |
|---|---|---|
| Test coverage | 80% | Blocks merge if below |
| Mutation score | 70% | Blocks merge if below |
| Cyclomatic complexity | 15 | Blocks merge if any function exceeds |
| Security lint severity | Medium+ (bandit) / any match (eslint-security) | Blocks merge |
| Dependency CVE severity | High / Critical | Blocks merge |
| Secrets | Any detected | Blocks merge + blocks all other security jobs |
| N+1 queries | Any detected | Blocks merge |
| Memory leak (runtime) | Any console.error on unmounted component | Blocks merge |

---

## Out of Scope

- Runtime memory profiling (`memray`) — not suitable for CI blocking gates
- Runtime race condition detection (asyncio debug mode) — static analysis sufficient for this stack
- ORM-level N+1 detection — project uses raw asyncpg; revisit if an ORM is introduced
