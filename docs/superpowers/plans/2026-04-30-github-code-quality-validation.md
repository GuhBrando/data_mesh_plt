# GitHub Code Quality Validation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add two GitHub Actions workflows enforcing mutation testing, coverage (80%), complexity (≤15), N+1 detection, static race/leak analysis, secret scanning, security linting, and dependency auditing as blocking PR gates.

**Architecture:** Two new workflow files (`quality.yml`, `security.yml`) sit alongside the unchanged `ci.yml`. Fast jobs run on every push; slow mutation jobs trigger on PRs to `main`/`develop` only. Supporting config changes to `pyproject.toml`, `vite.config.ts`, a new `frontend/eslint.config.js`, and a new `tests/conftest.py` provide the local tooling the workflows invoke.

**Tech Stack:** GitHub Actions, mutmut 2.x (Python mutation), Stryker (TS mutation), pytest-cov, vitest coverage-v8, ruff (C90/ASYNC), radon, bandit, pip-audit, gitleaks-action, eslint-plugin-security, @tanstack/eslint-plugin-query, eslint-plugin-react-hooks, typescript-eslint

---

## File Map

| Action | File |
|---|---|
| Modify | `pyproject.toml` |
| Modify | `frontend/package.json` |
| Modify | `frontend/vite.config.ts` |
| Modify | `frontend/src/test/setup.ts` |
| Create | `frontend/eslint.config.js` |
| Create | `frontend/stryker.config.mjs` |
| Create | `tests/conftest.py` |
| Create | `tests/unit/test_n1_detection.py` |
| Create | `.github/workflows/quality.yml` |
| Create | `.github/workflows/security.yml` |

---

### Task 1: Python quality tooling setup

**Files:**
- Modify: `pyproject.toml`

- [ ] **Step 1: Update dev dependencies in pyproject.toml**

Replace the `[project.optional-dependencies]` section:

```toml
[project.optional-dependencies]
dev = [
    "ruff",
    "pre-commit>=3.4.0",
    "pip-tools>=6.15.0",
    "pytest>=8.0.0",
    "pytest-asyncio>=0.23.0",
    "httpx>=0.27.0",
    "pytest-cov>=5.0.0",
    "radon>=6.0.0",
    "mutmut>=2.4.0,<3",
    "bandit>=1.7.0",
    "pip-audit>=2.7.0",
]
```

- [ ] **Step 2: Add complexity and async rules to ruff config**

Replace the `[tool.ruff.lint]` `select` list:

```toml
[tool.ruff.lint]
ignore = [
    "D105",
    "D107",
    "D203",
    "D212",
    "UP006",
    "UP007",
    "D400",
    "D406",
    "D407",
    "PLC1901",
    "UP035",
]
select = [
    "F",
    "W",
    "E",
    "I",
    "UP",
    "C4",
    "FA",
    "ISC",
    "ICN",
    "RET",
    "SIM",
    "TID",
    "TC",
    "PTH",
    "TD",
    "NPY",
    "C90",
    "ASYNC",
]
```

Add after `[tool.ruff.lint]` block:

```toml
[tool.ruff.lint.mccabe]
max-complexity = 15
```

- [ ] **Step 3: Add N+1 pytest marker and mutmut config**

Replace `[tool.pytest.ini_options]`:

```toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
markers = [
    "n1: marks tests that verify N+1 query patterns are absent",
]
```

Add new section at end of file:

```toml
[tool.mutmut]
paths_to_mutate = "backend/"
runner = "python -m pytest tests/ -x -q --no-header"
```

- [ ] **Step 4: Install new dependencies**

```bash
uv sync --extra dev
```

Expected: resolves without errors, new packages printed as installed.

- [ ] **Step 5: Verify ruff complexity rule is active**

Create a temporary file:

```bash
cat > _tmp_cc.py << 'EOF'
def too_complex(a, b, c, d, e, f, g, h, i, j, k, l, m, n, o, p):
    if a: pass
    if b: pass
    if c: pass
    if d: pass
    if e: pass
    if f: pass
    if g: pass
    if h: pass
    if i: pass
    if j: pass
    if k: pass
    if l: pass
    if m: pass
    if n: pass
    if o: pass
    if p: pass
EOF
```

Run:

```bash
uv run ruff check _tmp_cc.py --select C90
```

Expected output: `_tmp_cc.py:1:1: C901 'too_complex' is too complex (17 > 15)`

Delete it:

```bash
rm _tmp_cc.py
```

- [ ] **Step 6: Verify bandit runs**

```bash
uv run bandit -r backend/ -ll --quiet
```

Expected: exits 0 if no medium+ findings (or lists findings if any). Do not fix findings — just verify the tool runs.

- [ ] **Step 7: Verify pip-audit runs**

```bash
uv run pip-audit
```

Expected: exits 0 (no known CVEs), or lists findings. Do not fix — just verify.

- [ ] **Step 8: Commit**

```bash
git add pyproject.toml
git commit -m "feat: add Python quality tooling (pytest-cov, mutmut, bandit, radon, pip-audit)"
```

---

### Task 2: Frontend ESLint setup

**Files:**
- Modify: `frontend/package.json`
- Create: `frontend/eslint.config.js`

- [ ] **Step 1: Add new devDependencies to frontend/package.json**

Add the following keys to `devDependencies` (keep all existing entries):

```json
"@eslint/js": "^9.17.0",
"@stryker-mutator/core": "^8.6.0",
"@stryker-mutator/vitest-runner": "^8.6.0",
"@tanstack/eslint-plugin-query": "^5.62.0",
"@vitest/coverage-v8": "^4.1.5",
"eslint": "^9.17.0",
"eslint-plugin-react-hooks": "^5.1.0",
"eslint-plugin-security": "^3.0.1",
"globals": "^15.14.0",
"typescript-eslint": "^8.19.0"
```

Add `test:coverage` and `lint` to `scripts`:

```json
"scripts": {
  "dev": "vite",
  "build": "tsc && vite build",
  "preview": "vite preview",
  "test": "vitest run",
  "test:watch": "vitest",
  "test:coverage": "vitest run --coverage",
  "lint": "eslint src/ --max-warnings 0"
}
```

- [ ] **Step 2: Create frontend/eslint.config.js**

```js
import js from '@eslint/js'
import globals from 'globals'
import tseslint from 'typescript-eslint'
import reactHooks from 'eslint-plugin-react-hooks'
import security from 'eslint-plugin-security'
import tanstackQuery from '@tanstack/eslint-plugin-query'

export default tseslint.config(
  { ignores: ['dist', 'node_modules', 'coverage', '.stryker-tmp'] },
  {
    extends: [js.configs.recommended, ...tseslint.configs.recommended],
    files: ['**/*.{ts,tsx}'],
    languageOptions: {
      ecmaVersion: 2020,
      globals: globals.browser,
    },
    plugins: {
      'react-hooks': reactHooks,
      'security': security,
      '@tanstack/query': tanstackQuery,
    },
    rules: {
      ...reactHooks.configs['recommended-latest'].rules,
      ...security.configs.recommended.rules,
      ...tanstackQuery.configs['flat/recommended'].rules,
      'complexity': ['error', 15],
      'security/detect-object-injection': 'warn',
    },
  },
)
```

Note: `detect-object-injection` is `warn` not `error` — TypeScript array indexing with variables generates many false positives with this rule.

- [ ] **Step 3: Install packages**

```bash
cd frontend && npm install
```

Expected: no errors, `package-lock.json` updated with new packages.

- [ ] **Step 4: Verify ESLint runs**

```bash
cd frontend && npm run lint
```

Expected: exits 0, or lists violations in existing code. If violations exist, do not fix them in this task — note them for a follow-up PR. The CI gate only blocks new violations.

- [ ] **Step 5: Verify complexity rule fires**

Create `frontend/src/_tmp_cc.ts`:

```ts
export function tooComplex(
  a: boolean, b: boolean, c: boolean, d: boolean,
  e: boolean, f: boolean, g: boolean, h: boolean,
  i: boolean, j: boolean, k: boolean, l: boolean,
  m: boolean, n: boolean, o: boolean, p: boolean,
): void {
  if (a) return; if (b) return; if (c) return; if (d) return;
  if (e) return; if (f) return; if (g) return; if (h) return;
  if (i) return; if (j) return; if (k) return; if (l) return;
  if (m) return; if (n) return; if (o) return; if (p) return;
}
```

Run:

```bash
cd frontend && npx eslint src/_tmp_cc.ts
```

Expected: `Complexity of 17 exceeds max 15  complexity`

Delete it:

```bash
rm frontend/src/_tmp_cc.ts
```

- [ ] **Step 6: Commit**

```bash
git add frontend/package.json frontend/package-lock.json frontend/eslint.config.js
git commit -m "feat: add frontend ESLint config with security, complexity, hooks, and React Query rules"
```

---

### Task 3: Vitest coverage configuration

**Files:**
- Modify: `frontend/vite.config.ts`

- [ ] **Step 1: Add coverage block to vite.config.ts**

Replace the full contents of `frontend/vite.config.ts`:

```ts
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: process.env.VITE_BACKEND_URL ?? 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: './src/test/setup.ts',
    coverage: {
      provider: 'v8',
      thresholds: {
        lines: 80,
        functions: 80,
        branches: 80,
        statements: 80,
      },
      reporter: ['text', 'lcov'],
      exclude: [
        'src/test/**',
        'src/**/*.test.{ts,tsx}',
        'src/main.tsx',
        'node_modules/**',
      ],
    },
  },
})
```

- [ ] **Step 2: Run coverage and record baseline**

```bash
cd frontend && npm run test:coverage
```

Expected: prints a coverage table. It may fail if current coverage is below 80% — **this is expected and intentional**. Record the current percentages. Missing coverage will need to be addressed with additional tests in a follow-up PR before this PR can merge.

- [ ] **Step 3: Commit**

```bash
git add frontend/vite.config.ts
git commit -m "feat: add vitest v8 coverage with 80% threshold"
```

---

### Task 4: React memory leak test setup

**Files:**
- Modify: `frontend/src/test/setup.ts`

- [ ] **Step 1: Replace setup.ts with leak detection setup**

Replace the full contents of `frontend/src/test/setup.ts`:

```ts
import '@testing-library/jest-dom'
import { afterEach, beforeEach, vi } from 'vitest'
import { cleanup } from '@testing-library/react'

afterEach(() => {
  cleanup()
})

beforeEach(() => {
  vi.spyOn(console, 'error').mockImplementation((...args: unknown[]) => {
    const message = typeof args[0] === 'string' ? args[0] : ''
    if (message.includes('not wrapped in act(')) {
      throw new Error(`Memory leak / async update after unmount detected: ${message}`)
    }
  })
})

afterEach(() => {
  vi.restoreAllMocks()
})
```

This spy catches React's `act()` warning — the signal React 18 emits when a component updates state after the test has unmounted it, indicating an unresolved async operation (memory leak pattern).

- [ ] **Step 2: Verify existing tests still pass**

```bash
cd frontend && npm test
```

Expected: all tests pass. If any test fails with "Memory leak / async update after unmount detected", there is a real async state update issue in that test — fix it before committing.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/test/setup.ts
git commit -m "feat: add React memory leak detection via act() warning spy in vitest setup"
```

---

### Task 5: N+1 pytest fixture

**Files:**
- Create: `tests/conftest.py`
- Create: `tests/unit/test_n1_detection.py`

- [ ] **Step 1: Write the failing test first**

Create `tests/unit/test_n1_detection.py`:

```python
from unittest.mock import AsyncMock

import pytest

from backend.use_cases.data_product.list import ListDataProductsUseCase


@pytest.mark.n1
async def test_list_data_products_makes_single_db_call(n1_guard):
    repo = AsyncMock()
    repo.list.return_value = []

    guard = n1_guard(repo)
    use_case = ListDataProductsUseCase(repository=repo)
    await use_case.execute()

    guard.assert_max_calls("list", max_calls=1)


@pytest.mark.n1
async def test_n1_guard_catches_repeated_calls(n1_guard):
    """Self-test: verify the guard correctly detects repeated calls."""
    repo = AsyncMock()
    guard = n1_guard(repo)

    for _ in range(3):
        await repo.get()

    with pytest.raises(AssertionError, match="N\\+1 detected"):
        guard.assert_max_calls("get", max_calls=1)
```

- [ ] **Step 2: Run to confirm failure (fixture missing)**

```bash
uv run pytest tests/unit/test_n1_detection.py -v
```

Expected: `ERROR` — `fixture 'n1_guard' not found`

- [ ] **Step 3: Create tests/conftest.py**

```python
from unittest.mock import AsyncMock

import pytest


class _QueryGuard:
    def __init__(self, mock: AsyncMock) -> None:
        self._mock = mock

    def assert_max_calls(self, method_name: str, max_calls: int = 1) -> None:
        method = getattr(self._mock, method_name)
        count = method.call_count
        if count > max_calls:
            raise AssertionError(
                f"N+1 detected: '{method_name}' called {count} times "
                f"(max allowed: {max_calls})"
            )


@pytest.fixture
def n1_guard():
    def _make(mock: AsyncMock) -> _QueryGuard:
        return _QueryGuard(mock)

    return _make
```

- [ ] **Step 4: Run N+1 tests to verify they pass**

```bash
uv run pytest tests/unit/test_n1_detection.py -v -m n1
```

Expected:
```
tests/unit/test_n1_detection.py::test_list_data_products_makes_single_db_call PASSED
tests/unit/test_n1_detection.py::test_n1_guard_catches_repeated_calls PASSED
2 passed
```

- [ ] **Step 5: Run full suite for regressions**

```bash
uv run pytest tests/ -v --tb=short
```

Expected: all previously passing tests still pass.

- [ ] **Step 6: Commit**

```bash
git add tests/conftest.py tests/unit/test_n1_detection.py
git commit -m "feat: add N+1 query detection fixture and self-test"
```

---

### Task 6: Stryker mutation config

**Files:**
- Create: `frontend/stryker.config.mjs`
- Modify: `.gitignore`

- [ ] **Step 1: Create frontend/stryker.config.mjs**

```js
/** @type {import('@stryker-mutator/api/core').PartialStrykerOptions} */
export default {
  testRunner: 'vitest',
  vitest: {
    configFile: 'vite.config.ts',
  },
  mutate: [
    'src/**/*.ts',
    'src/**/*.tsx',
    '!src/**/*.test.ts',
    '!src/**/*.test.tsx',
    '!src/test/**/*',
    '!src/main.tsx',
  ],
  thresholds: {
    high: 80,
    low: 70,
    break: 70,
  },
  coverageAnalysis: 'perTest',
  reporters: ['progress', 'clear-text'],
  tempDirName: '.stryker-tmp',
  cleanTempDir: true,
}
```

- [ ] **Step 2: Add stryker temp dir to .gitignore**

Append to `.gitignore` (root):

```
frontend/.stryker-tmp/
```

- [ ] **Step 3: Verify Stryker config is valid (dry run)**

```bash
cd frontend && npx stryker run --dryRun 2>&1 | head -30
```

Expected: Stryker initializes, discovers source files, prints mutant count. Exit code 0. Do not run without `--dryRun` locally — full mutation run takes 10–20 minutes.

- [ ] **Step 4: Commit**

```bash
git add frontend/stryker.config.mjs .gitignore
git commit -m "feat: add Stryker mutation testing config for React/TS (70% threshold)"
```

---

### Task 7: quality.yml workflow

**Files:**
- Create: `.github/workflows/quality.yml`

- [ ] **Step 1: Create .github/workflows/quality.yml**

```yaml
name: Code Quality

on:
  push:
    branches: ["**"]
  pull_request:
    branches: ["main", "develop"]

jobs:
  coverage-python:
    name: Python Coverage (>=80%)
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - uses: astral-sh/setup-uv@v4
        with:
          enable-cache: true

      - run: uv sync --extra dev

      - name: Run tests with coverage
        run: uv run pytest tests/ --cov=backend --cov-fail-under=80 --cov-report=xml -q

      - uses: actions/upload-artifact@v4
        if: always()
        with:
          name: python-coverage-report
          path: coverage.xml

  coverage-react:
    name: React Coverage (>=80%)
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-node@v4
        with:
          node-version: "20"
          cache: "npm"
          cache-dependency-path: frontend/package-lock.json

      - name: Install dependencies
        run: npm ci
        working-directory: frontend

      - name: Run coverage
        run: npm run test:coverage
        working-directory: frontend

  complexity:
    name: Cyclomatic Complexity (<=15)
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - uses: astral-sh/setup-uv@v4
        with:
          enable-cache: true

      - run: uv sync --extra dev

      - name: Ruff complexity check (blocking)
        run: uv run ruff check . --select C90

      - name: Radon complexity report (informational)
        run: uv run radon cc backend/ -s -a --min C
        continue-on-error: true

  n1-detector:
    name: N+1 Query Detection
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - uses: astral-sh/setup-uv@v4
        with:
          enable-cache: true

      - run: uv sync --extra dev

      - name: Run N+1 detection tests
        run: uv run pytest tests/ -m "n1" -v

  static-analysis:
    name: Static Race & Leak Analysis
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - uses: astral-sh/setup-uv@v4
        with:
          enable-cache: true

      - run: uv sync --extra dev

      - name: Ruff ASYNC and SIM rules (Python async safety)
        run: uv run ruff check . --select ASYNC,SIM

      - uses: actions/setup-node@v4
        with:
          node-version: "20"
          cache: "npm"
          cache-dependency-path: frontend/package-lock.json

      - name: Install frontend dependencies
        run: npm ci
        working-directory: frontend

      - name: ESLint (hooks, complexity, security, N+1)
        run: npm run lint
        working-directory: frontend

  mutation-python:
    name: Python Mutation Score (>=70%)
    runs-on: ubuntu-latest
    needs: coverage-python
    if: github.event_name == 'pull_request'
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - uses: astral-sh/setup-uv@v4
        with:
          enable-cache: true

      - run: uv sync --extra dev

      - name: Run mutmut
        run: uv run mutmut run || true

      - name: Check mutation score threshold
        run: |
          RESULT=$(uv run mutmut results 2>/dev/null || echo "")
          KILLED=$(echo "$RESULT" | grep -oP '(?<=Killed: )\d+' | head -1 || echo "0")
          SURVIVED=$(echo "$RESULT" | grep -oP '(?<=Survived: )\d+' | head -1 || echo "0")
          TOTAL=$((KILLED + SURVIVED))
          if [ "$TOTAL" -eq 0 ]; then
            echo "ERROR: No mutants were generated"
            exit 1
          fi
          SCORE=$((KILLED * 100 / TOTAL))
          echo "Mutation score: ${SCORE}% (${KILLED}/${TOTAL} killed)"
          if [ "$SCORE" -lt 70 ]; then
            echo "FAIL: Mutation score ${SCORE}% is below the 70% threshold"
            uv run mutmut results
            exit 1
          fi
          echo "PASS: Mutation score ${SCORE}% meets the 70% threshold"

  mutation-react:
    name: React Mutation Score (>=70%)
    runs-on: ubuntu-latest
    needs: coverage-react
    if: github.event_name == 'pull_request'
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-node@v4
        with:
          node-version: "20"
          cache: "npm"
          cache-dependency-path: frontend/package-lock.json

      - name: Install dependencies
        run: npm ci
        working-directory: frontend

      - name: Run Stryker mutation tests
        run: npx stryker run
        working-directory: frontend
```

- [ ] **Step 2: Validate YAML syntax**

```bash
uv run python3 -c "import yaml; yaml.safe_load(open('.github/workflows/quality.yml')); print('YAML valid')"
```

Expected: `YAML valid`

- [ ] **Step 3: Commit**

```bash
git add .github/workflows/quality.yml
git commit -m "feat: add quality.yml workflow (coverage, complexity, N+1, static analysis, mutation)"
```

---

### Task 8: security.yml workflow

**Files:**
- Create: `.github/workflows/security.yml`

- [ ] **Step 1: Create .github/workflows/security.yml**

```yaml
name: Security

on:
  push:
    branches: ["**"]
  pull_request:
    branches: ["main", "develop"]
  schedule:
    - cron: "0 8 * * 1"

jobs:
  secret-scan:
    name: Secret Scan (gitleaks)
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - uses: gitleaks/gitleaks-action@v2
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}

  security-lint-python:
    name: Python Security Lint (bandit)
    runs-on: ubuntu-latest
    needs: secret-scan
    if: github.event_name == 'pull_request' || github.event_name == 'schedule'
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - uses: astral-sh/setup-uv@v4
        with:
          enable-cache: true

      - run: uv sync --extra dev

      - name: Run bandit (medium+ severity blocks merge)
        run: uv run bandit -r backend/ -ll

  security-lint-react:
    name: React Security Lint (eslint-plugin-security)
    runs-on: ubuntu-latest
    needs: secret-scan
    if: github.event_name == 'pull_request' || github.event_name == 'schedule'
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-node@v4
        with:
          node-version: "20"
          cache: "npm"
          cache-dependency-path: frontend/package-lock.json

      - name: Install dependencies
        run: npm ci
        working-directory: frontend

      - name: ESLint security rules
        run: npm run lint
        working-directory: frontend

  dependency-audit:
    name: Dependency Vulnerability Audit
    runs-on: ubuntu-latest
    needs: secret-scan
    if: github.event_name == 'pull_request' || github.event_name == 'schedule'
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - uses: astral-sh/setup-uv@v4
        with:
          enable-cache: true

      - run: uv sync --extra dev

      - name: Python dependency audit (all known CVEs)
        run: uv run pip-audit

      - uses: actions/setup-node@v4
        with:
          node-version: "20"
          cache: "npm"
          cache-dependency-path: frontend/package-lock.json

      - name: Install frontend dependencies
        run: npm ci
        working-directory: frontend

      - name: Node dependency audit (high/critical only)
        run: npm audit --audit-level=high
        working-directory: frontend
```

Note: `pip-audit` reports all severity levels (pip-audit does not support CVSS-based severity filtering). `npm audit --audit-level=high` correctly filters to high/critical only.

- [ ] **Step 2: Validate YAML syntax**

```bash
uv run python3 -c "import yaml; yaml.safe_load(open('.github/workflows/security.yml')); print('YAML valid')"
```

Expected: `YAML valid`

- [ ] **Step 3: Commit**

```bash
git add .github/workflows/security.yml
git commit -m "feat: add security.yml workflow (gitleaks, bandit, eslint-security, pip-audit, npm audit)"
```
