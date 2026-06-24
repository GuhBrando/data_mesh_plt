# Per-Product GitHub Repository Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Provision a dedicated private GitHub repository for every Data Product entity (on create, lazily on access, archive on delete) without changing the existing central contracts repository flow.

**Architecture:** Router-level orchestration mirroring the existing `_push_to_github` pattern in `backend/interface/routers/data_contract.py`. Use cases stay pure DB logic; `GitHubClient` gains three new methods (`create_product_repo`, `push_scaffold`, `archive_repo`); `DataProduct` gains `repo_url: str | None`; failures are warn-only and lazily retried on next read/update.

**Tech Stack:** Python 3.12, FastAPI, asyncpg, httpx, pytest with `asyncio_mode=auto`, Atlas migrations.

**Reference spec:** `docs/superpowers/specs/2026-06-10-per-product-github-repo-design.md`

---

## File Structure

**Create:**
- `database/migrations/20260610000001_data_products_repo_url.sql` — add nullable `repo_url` column.
- `tests/unit/infra/__init__.py` — empty package marker (if missing).
- `tests/unit/infra/test_github_client.py` — unit tests for new client methods.

**Modify:**
- `backend/domain/entities/data_product.py` — add `repo_url: str | None`.
- `backend/domain/interfaces/data_product_repository.py` — add `update_repo_url` abstract method.
- `backend/infra/repositories/data_product_repository.py` — return `repo_url` from all SELECTs; implement `update_repo_url`.
- `backend/interface/schemas/data_product.py` — add `repo_url` to `DataProductResponseModel`.
- `backend/infra/github_client.py` — add `create_product_repo`, `push_scaffold`, `archive_repo`; add owner-type detection.
- `backend/interface/routers/data_product.py` — add `_ensure_product_repo`, `_build_scaffold`, `_archive_product_repo`; wire to POST/GET-detail/PUT/DELETE.
- `tests/unit/interface/test_data_product_router.py` — add tests for the new GitHub touch points.

---

## Task 1: Add `repo_url` column and entity field

**Files:**
- Create: `database/migrations/20260610000001_data_products_repo_url.sql`
- Modify: `backend/domain/entities/data_product.py`

- [ ] **Step 1: Write the migration**

```sql
-- =============================================================================
-- Add nullable repo_url column to catalog.data_products to store the URL of the
-- dedicated GitHub repository provisioned for each data product. Nullable so
-- existing rows are valid and so warn-only provisioning failures leave the row
-- in a recoverable state (the lazy-backfill path will fill it on next access).
-- =============================================================================

ALTER TABLE catalog.data_products
    ADD COLUMN repo_url TEXT;
```

- [ ] **Step 2: Extend the `DataProduct` entity**

Replace the entire body of `backend/domain/entities/data_product.py` with:

```python
import uuid
from datetime import datetime


class DataProduct:
    def __init__(
        self,
        id: uuid.UUID,
        name: str,
        description: str,
        data_contracts_id: uuid.UUID,
        created_at: datetime,
        updated_at: datetime,
        repo_url: str | None = None,
    ):
        self.id = id
        self.name = name
        self.description = description
        self.data_contracts_id = data_contracts_id
        self.created_at = created_at
        self.updated_at = updated_at
        self.repo_url = repo_url
```

- [ ] **Step 3: Verify existing tests still pass**

Run: `pytest tests/unit/ -q`

Expected: PASS — `repo_url` has a default of `None`, so existing constructors (including the one in `tests/unit/interface/test_data_product_router.py`) keep working.

- [ ] **Step 4: Commit**

```bash
git add database/migrations/20260610000001_data_products_repo_url.sql backend/domain/entities/data_product.py
git commit -m "feat: add repo_url to data_products and DataProduct entity"
```

---

## Task 2: Repository — return and update `repo_url`

**Files:**
- Modify: `backend/domain/interfaces/data_product_repository.py`
- Modify: `backend/infra/repositories/data_product_repository.py`

- [ ] **Step 1: Add the abstract method to the interface**

In `backend/domain/interfaces/data_product_repository.py`, add the following method to `IDataProductRepository` (place it after `delete`):

```python
    @abstractmethod
    async def update_repo_url(
        self, product_id: uuid.UUID, repo_url: str
    ) -> None: ...
```

- [ ] **Step 2: Update the Postgres SELECTs and implement `update_repo_url`**

Replace the entire body of `backend/infra/repositories/data_product_repository.py` with:

```python
import uuid

from backend.domain.entities.data_product import DataProduct
from backend.domain.interfaces.data_product_repository import IDataProductRepository

_RETURNING = (
    "id, name, description, data_contracts_id, repo_url, created_at, updated_at"
)


def _row_to_entity(row) -> DataProduct:
    return DataProduct(
        id=row["id"],
        name=row["name"],
        description=row["description"],
        data_contracts_id=row["data_contracts_id"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
        repo_url=row["repo_url"],
    )


class PostgresDataProductRepository(IDataProductRepository):
    def __init__(self, db):
        self.db = db

    async def create(
        self, name: str, description: str, data_contracts_id: uuid.UUID
    ) -> DataProduct:
        async with self.db.transaction():
            row = await self.db.fetchrow(
                f"""
                INSERT INTO catalog.data_products (name, description, data_contracts_id)
                VALUES ($1, $2, $3)
                RETURNING {_RETURNING};
                """,
                name,
                description,
                data_contracts_id,
            )
            return _row_to_entity(row)

    async def get_by_id(self, product_id: uuid.UUID) -> DataProduct | None:
        row = await self.db.fetchrow(
            f"""
            SELECT {_RETURNING}
            FROM catalog.data_products WHERE id = $1;
            """,
            product_id,
        )
        return _row_to_entity(row) if row else None

    async def list(self) -> list[DataProduct]:
        rows = await self.db.fetch(
            f"SELECT {_RETURNING} FROM catalog.data_products;"
        )
        return [_row_to_entity(r) for r in rows]

    async def update(
        self,
        product_id: uuid.UUID,
        name: str | None,
        description: str | None,
        data_contracts_id: uuid.UUID | None,
    ) -> DataProduct | None:
        updates: dict = {}
        if name is not None:
            updates["name"] = name
        if description is not None:
            updates["description"] = description
        if data_contracts_id is not None:
            updates["data_contracts_id"] = data_contracts_id

        if not updates:
            return await self.get_by_id(product_id)

        set_clauses = ", ".join(f"{col} = ${i + 1}" for i, col in enumerate(updates))
        values = list(updates.values()) + [product_id]

        async with self.db.transaction():
            row = await self.db.fetchrow(
                f"""
                UPDATE catalog.data_products
                SET {set_clauses}, updated_at = now()
                WHERE id = ${len(values)}
                RETURNING {_RETURNING};
                """,
                *values,
            )
            return _row_to_entity(row) if row else None

    async def delete(self, product_id: uuid.UUID) -> bool:
        async with self.db.transaction():
            result = await self.db.execute(
                "DELETE FROM catalog.data_products WHERE id = $1;",
                product_id,
            )
            return result == "DELETE 1"

    async def update_repo_url(
        self, product_id: uuid.UUID, repo_url: str
    ) -> None:
        async with self.db.transaction():
            await self.db.execute(
                "UPDATE catalog.data_products SET repo_url = $1 WHERE id = $2;",
                repo_url,
                product_id,
            )
```

- [ ] **Step 3: Run existing unit tests**

Run: `pytest tests/unit/ -q`

Expected: PASS — `_row_to_entity` only adds an extra kwarg that defaults from the row mapping, and existing tests do not exercise the new interface method directly.

- [ ] **Step 4: Commit**

```bash
git add backend/domain/interfaces/data_product_repository.py backend/infra/repositories/data_product_repository.py
git commit -m "feat: select and update repo_url on data_products repository"
```

---

## Task 3: Expose `repo_url` on the response schema

**Files:**
- Modify: `backend/interface/schemas/data_product.py`
- Test: `tests/unit/interface/test_data_product_router.py`

- [ ] **Step 1: Add `repo_url` to the response model**

Replace the entire body of `backend/interface/schemas/data_product.py` with:

```python
import uuid
from datetime import datetime

from pydantic import BaseModel


class DataProductCreateModel(BaseModel):
    name: str
    description: str
    data_contracts_id: uuid.UUID


class DataProductResponseModel(BaseModel):
    id: uuid.UUID
    name: str
    description: str
    data_contracts_id: uuid.UUID
    repo_url: str | None = None
    created_at: datetime
    updated_at: datetime


class DataProductUpdateModel(BaseModel):
    name: str | None = None
    description: str | None = None
    data_contracts_id: uuid.UUID | None = None
```

- [ ] **Step 2: Wire `repo_url` through the existing router `_to_response`**

In `backend/interface/routers/data_product.py`, replace the `_to_response` helper with:

```python
def _to_response(product: DataProduct) -> DataProductResponseModel:
    return DataProductResponseModel(
        id=product.id,
        name=product.name,
        description=product.description,
        data_contracts_id=product.data_contracts_id,
        repo_url=product.repo_url,
        created_at=product.created_at,
        updated_at=product.updated_at,
    )
```

- [ ] **Step 3: Add a router test asserting `repo_url` is on the response**

Append the following test to `tests/unit/interface/test_data_product_router.py`:

```python
def test_get_data_product_includes_repo_url(admin_client):
    mock_uc = AsyncMock()
    mock_uc.execute.return_value = _product()
    mock_uc.execute.return_value.repo_url = "https://github.com/acme/dp-x"
    app.dependency_overrides[get_get_data_product_use_case] = lambda: mock_uc
    resp = admin_client.get(f"/api/v1/data-products/{PRODUCT_ID}")
    assert resp.status_code == 200
    assert resp.json()["repo_url"] == "https://github.com/acme/dp-x"
```

- [ ] **Step 4: Run the test**

Run: `pytest tests/unit/interface/test_data_product_router.py -q`

Expected: PASS for all tests, including the new one.

- [ ] **Step 5: Commit**

```bash
git add backend/interface/schemas/data_product.py backend/interface/routers/data_product.py tests/unit/interface/test_data_product_router.py
git commit -m "feat: expose repo_url on data product response"
```

---

## Task 4: `GitHubClient.create_product_repo` with owner-type detection

**Files:**
- Modify: `backend/infra/github_client.py`
- Create: `tests/unit/infra/__init__.py` (if not present)
- Create: `tests/unit/infra/test_github_client.py`

- [ ] **Step 1: Ensure test package exists**

If `tests/unit/infra/__init__.py` does not exist, create it as an empty file. This makes pytest discover it as a package.

- [ ] **Step 2: Write the failing test**

Create `tests/unit/infra/test_github_client.py` with:

```python
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from backend.infra.github_client import GitHubClient


def _resp(status: int, json_body: dict | None = None) -> MagicMock:
    r = MagicMock(spec=httpx.Response)
    r.status_code = status
    r.is_success = 200 <= status < 300
    r.json.return_value = json_body or {}
    r.text = str(json_body or "")
    return r


@pytest.fixture
def client():
    return GitHubClient(token="t", repo="acme/contracts")


def _async_client_ctx(mock_client):
    ctx = MagicMock()
    ctx.__aenter__ = AsyncMock(return_value=mock_client)
    ctx.__aexit__ = AsyncMock(return_value=False)
    return ctx


async def test_create_product_repo_user_owner_posts_to_user_repos(client):
    mock_http = AsyncMock()
    mock_http.get = AsyncMock(
        return_value=_resp(200, {"type": "User", "login": "acme"})
    )
    mock_http.post = AsyncMock(
        return_value=_resp(
            201, {"html_url": "https://github.com/acme/dp-x", "full_name": "acme/dp-x"}
        )
    )
    with patch(
        "backend.infra.github_client.httpx.AsyncClient",
        return_value=_async_client_ctx(mock_http),
    ):
        result = await client.create_product_repo("dp-x", "desc")
    assert result["html_url"] == "https://github.com/acme/dp-x"
    assert result["full_name"] == "acme/dp-x"
    mock_http.post.assert_awaited_once()
    posted_url = mock_http.post.await_args.args[0]
    assert posted_url.endswith("/user/repos")


async def test_create_product_repo_org_owner_posts_to_orgs_repos(client):
    mock_http = AsyncMock()
    mock_http.get = AsyncMock(
        return_value=_resp(200, {"type": "Organization", "login": "acme"})
    )
    mock_http.post = AsyncMock(
        return_value=_resp(
            201, {"html_url": "https://github.com/acme/dp-x", "full_name": "acme/dp-x"}
        )
    )
    with patch(
        "backend.infra.github_client.httpx.AsyncClient",
        return_value=_async_client_ctx(mock_http),
    ):
        await client.create_product_repo("dp-x", "desc")
    posted_url = mock_http.post.await_args.args[0]
    assert posted_url.endswith("/orgs/acme/repos")


async def test_create_product_repo_owner_type_cached(client):
    mock_http = AsyncMock()
    mock_http.get = AsyncMock(
        return_value=_resp(200, {"type": "User", "login": "acme"})
    )
    mock_http.post = AsyncMock(
        return_value=_resp(
            201, {"html_url": "https://github.com/acme/dp-x", "full_name": "acme/dp-x"}
        )
    )
    with patch(
        "backend.infra.github_client.httpx.AsyncClient",
        return_value=_async_client_ctx(mock_http),
    ):
        await client.create_product_repo("dp-x", "desc")
        await client.create_product_repo("dp-y", "desc")
    # Owner-detection GET should happen only once across both calls.
    assert mock_http.get.await_count == 1


async def test_create_product_repo_adopts_existing_on_422(client):
    mock_http = AsyncMock()
    mock_http.get = AsyncMock(
        side_effect=[
            _resp(200, {"type": "User", "login": "acme"}),
            _resp(
                200,
                {"html_url": "https://github.com/acme/dp-x", "full_name": "acme/dp-x"},
            ),
        ]
    )
    mock_http.post = AsyncMock(
        return_value=_resp(422, {"errors": [{"message": "name already exists"}]})
    )
    with patch(
        "backend.infra.github_client.httpx.AsyncClient",
        return_value=_async_client_ctx(mock_http),
    ):
        result = await client.create_product_repo("dp-x", "desc")
    assert result["full_name"] == "acme/dp-x"


async def test_create_product_repo_raises_on_other_failure(client):
    mock_http = AsyncMock()
    mock_http.get = AsyncMock(
        return_value=_resp(200, {"type": "User", "login": "acme"})
    )
    mock_http.post = AsyncMock(return_value=_resp(500, {"message": "boom"}))
    with patch(
        "backend.infra.github_client.httpx.AsyncClient",
        return_value=_async_client_ctx(mock_http),
    ):
        with pytest.raises(RuntimeError):
            await client.create_product_repo("dp-x", "desc")
```

- [ ] **Step 3: Run the test to verify it fails**

Run: `pytest tests/unit/infra/test_github_client.py -q`

Expected: FAIL with `AttributeError: 'GitHubClient' object has no attribute 'create_product_repo'`.

- [ ] **Step 4: Implement the method**

In `backend/infra/github_client.py`, add the following imports at the top (preserve the existing ones):

```python
import base64
import logging
import re

import httpx
```

Replace the `GitHubClient` class with the following (keeps existing methods, adds `_owner`, `_owner_type`, `_get_owner_type`, `create_product_repo`):

```python
class GitHubClient:
    def __init__(self, token: str, repo: str):
        self._repo = repo
        self._owner = repo.split("/", 1)[0]
        self._owner_type: str | None = None
        self._headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

    def contract_path(self, domain: str, title: str) -> str:
        return f"contracts/{_slugify(domain)}/{_slugify(title)}.yaml"

    async def _get_sha(self, client: httpx.AsyncClient, path: str) -> str | None:
        r = await client.get(
            f"{_API}/repos/{self._repo}/contents/{path}",
            headers=self._headers,
        )
        if r.status_code == 200:
            return r.json().get("sha")
        return None

    @staticmethod
    def _raise_for_status(r: httpx.Response) -> None:
        if not r.is_success:
            raise RuntimeError(f"GitHub API {r.status_code}: {r.text}")

    async def push(self, path: str, content: str, message: str) -> None:
        async with httpx.AsyncClient(timeout=10.0) as client:
            sha = await self._get_sha(client, path)
            payload: dict = {
                "message": message,
                "content": base64.b64encode(content.encode()).decode(),
            }
            if sha:
                payload["sha"] = sha
            r = await client.put(
                f"{_API}/repos/{self._repo}/contents/{path}",
                headers=self._headers,
                json=payload,
            )
            self._raise_for_status(r)

    async def delete(self, path: str, message: str) -> None:
        async with httpx.AsyncClient(timeout=10.0) as client:
            sha = await self._get_sha(client, path)
            if sha is None:
                return
            r = await client.request(
                "DELETE",
                f"{_API}/repos/{self._repo}/contents/{path}",
                headers=self._headers,
                json={"message": message, "sha": sha},
            )
            self._raise_for_status(r)

    async def list_all_yaml_contents(self) -> list[tuple[str, str]]:
        async with httpx.AsyncClient(timeout=15.0) as client:
            r = await client.get(
                f"{_API}/repos/{self._repo}/git/trees/HEAD?recursive=1",
                headers=self._headers,
            )
            if r.status_code != 200:
                return []
            tree = r.json().get("tree", [])
            blobs = [
                i
                for i in tree
                if i["path"].startswith("contracts/")
                and i["path"].endswith(".yaml")
                and i["type"] == "blob"
            ]
            results: list[tuple[str, str]] = []
            for item in blobs:
                blob_r = await client.get(item["url"], headers=self._headers)
                if blob_r.status_code == 200:
                    raw = blob_r.json().get("content", "")
                    content = base64.b64decode(raw.replace("\n", "")).decode()
                    results.append((item["path"], content))
            return results

    async def _get_owner_type(self, client: httpx.AsyncClient) -> str:
        if self._owner_type is not None:
            return self._owner_type
        r = await client.get(
            f"{_API}/users/{self._owner}",
            headers=self._headers,
        )
        self._raise_for_status(r)
        self._owner_type = r.json().get("type", "User")
        return self._owner_type

    async def create_product_repo(self, name: str, description: str) -> dict:
        async with httpx.AsyncClient(timeout=15.0) as client:
            owner_type = await self._get_owner_type(client)
            url = (
                f"{_API}/orgs/{self._owner}/repos"
                if owner_type == "Organization"
                else f"{_API}/user/repos"
            )
            payload = {
                "name": name,
                "description": description,
                "private": True,
                "auto_init": False,
            }
            r = await client.post(url, headers=self._headers, json=payload)
            if r.status_code == 422 and "already exists" in r.text:
                existing = await client.get(
                    f"{_API}/repos/{self._owner}/{name}",
                    headers=self._headers,
                )
                self._raise_for_status(existing)
                data = existing.json()
                return {
                    "html_url": data["html_url"],
                    "full_name": data["full_name"],
                }
            self._raise_for_status(r)
            data = r.json()
            return {
                "html_url": data["html_url"],
                "full_name": data["full_name"],
            }
```

- [ ] **Step 5: Run the test to verify it passes**

Run: `pytest tests/unit/infra/test_github_client.py -q`

Expected: PASS for all five tests.

- [ ] **Step 6: Commit**

```bash
git add backend/infra/github_client.py tests/unit/infra/test_github_client.py tests/unit/infra/__init__.py
git commit -m "feat: GitHubClient.create_product_repo with owner-type detection"
```

---

## Task 5: `GitHubClient.push_scaffold`

**Files:**
- Modify: `backend/infra/github_client.py`
- Modify: `tests/unit/infra/test_github_client.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/unit/infra/test_github_client.py`:

```python
async def test_push_scaffold_puts_each_file(client):
    mock_http = AsyncMock()
    mock_http.get = AsyncMock(return_value=_resp(404))  # no existing sha
    mock_http.put = AsyncMock(return_value=_resp(201, {}))
    with patch(
        "backend.infra.github_client.httpx.AsyncClient",
        return_value=_async_client_ctx(mock_http),
    ):
        await client.push_scaffold(
            "acme/dp-x",
            {"README.md": "hello", "pipeline/.gitkeep": ""},
        )
    assert mock_http.put.await_count == 2
    urls = {call.args[0] for call in mock_http.put.await_args_list}
    assert any(u.endswith("/contents/README.md") for u in urls)
    assert any(u.endswith("/contents/pipeline/.gitkeep") for u in urls)


async def test_push_scaffold_raises_on_failure(client):
    mock_http = AsyncMock()
    mock_http.get = AsyncMock(return_value=_resp(404))
    mock_http.put = AsyncMock(return_value=_resp(500, {"message": "boom"}))
    with patch(
        "backend.infra.github_client.httpx.AsyncClient",
        return_value=_async_client_ctx(mock_http),
    ):
        with pytest.raises(RuntimeError):
            await client.push_scaffold("acme/dp-x", {"README.md": "hello"})
```

- [ ] **Step 2: Run to confirm failure**

Run: `pytest tests/unit/infra/test_github_client.py -q`

Expected: FAIL with `AttributeError: 'GitHubClient' object has no attribute 'push_scaffold'`.

- [ ] **Step 3: Implement `push_scaffold`**

In `backend/infra/github_client.py`, add this method to `GitHubClient` (immediately after `create_product_repo`):

```python
    async def push_scaffold(
        self, repo_full_name: str, files: dict[str, str]
    ) -> None:
        async with httpx.AsyncClient(timeout=15.0) as client:
            for path, content in files.items():
                sha_r = await client.get(
                    f"{_API}/repos/{repo_full_name}/contents/{path}",
                    headers=self._headers,
                )
                payload: dict = {
                    "message": f"Scaffold {path}",
                    "content": base64.b64encode(content.encode()).decode(),
                }
                if sha_r.status_code == 200:
                    payload["sha"] = sha_r.json().get("sha")
                r = await client.put(
                    f"{_API}/repos/{repo_full_name}/contents/{path}",
                    headers=self._headers,
                    json=payload,
                )
                self._raise_for_status(r)
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `pytest tests/unit/infra/test_github_client.py -q`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/infra/github_client.py tests/unit/infra/test_github_client.py
git commit -m "feat: GitHubClient.push_scaffold for initial product repo files"
```

---

## Task 6: `GitHubClient.archive_repo`

**Files:**
- Modify: `backend/infra/github_client.py`
- Modify: `tests/unit/infra/test_github_client.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/unit/infra/test_github_client.py`:

```python
async def test_archive_repo_patches_archived_true(client):
    mock_http = AsyncMock()
    mock_http.patch = AsyncMock(return_value=_resp(200, {"archived": True}))
    with patch(
        "backend.infra.github_client.httpx.AsyncClient",
        return_value=_async_client_ctx(mock_http),
    ):
        await client.archive_repo("acme/dp-x")
    mock_http.patch.assert_awaited_once()
    url = mock_http.patch.await_args.args[0]
    assert url.endswith("/repos/acme/dp-x")
    body = mock_http.patch.await_args.kwargs["json"]
    assert body == {"archived": True}


async def test_archive_repo_raises_on_failure(client):
    mock_http = AsyncMock()
    mock_http.patch = AsyncMock(return_value=_resp(500, {"message": "boom"}))
    with patch(
        "backend.infra.github_client.httpx.AsyncClient",
        return_value=_async_client_ctx(mock_http),
    ):
        with pytest.raises(RuntimeError):
            await client.archive_repo("acme/dp-x")
```

- [ ] **Step 2: Run to confirm failure**

Run: `pytest tests/unit/infra/test_github_client.py -q`

Expected: FAIL with `AttributeError: 'GitHubClient' object has no attribute 'archive_repo'`.

- [ ] **Step 3: Implement `archive_repo`**

In `backend/infra/github_client.py`, add to `GitHubClient` (immediately after `push_scaffold`):

```python
    async def archive_repo(self, repo_full_name: str) -> None:
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.patch(
                f"{_API}/repos/{repo_full_name}",
                headers=self._headers,
                json={"archived": True},
            )
            self._raise_for_status(r)
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `pytest tests/unit/infra/test_github_client.py -q`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/infra/github_client.py tests/unit/infra/test_github_client.py
git commit -m "feat: GitHubClient.archive_repo"
```

---

## Task 7: Router helpers `_build_scaffold` and `_ensure_product_repo`

**Files:**
- Modify: `backend/interface/routers/data_product.py`

This task adds the helpers but does NOT yet wire them to any endpoint. Wiring happens in Tasks 8–11.

- [ ] **Step 1: Add imports and helpers**

Replace the import block at the top of `backend/interface/routers/data_product.py` with:

```python
import logging
import re
import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException

from backend.domain.entities.data_product import DataProduct
from backend.domain.entities.user import User
from backend.domain.interfaces.data_contract_repository import IDataContractRepository
from backend.domain.interfaces.data_product_repository import IDataProductRepository
from backend.infra.github_client import GitHubClient
from backend.interface.dependencies import (
    get_create_data_product_use_case,
    get_data_contract_repository,
    get_data_product_repository,
    get_delete_data_product_use_case,
    get_get_data_product_use_case,
    get_github_client,
    get_list_data_products_use_case,
    get_update_data_product_use_case,
)
from backend.interface.schemas.data_product import (
    DataProductCreateModel,
    DataProductResponseModel,
    DataProductUpdateModel,
)
from backend.interface.security import get_current_user
from backend.use_cases.data_product.create import CreateDataProductUseCase
from backend.use_cases.data_product.delete import DeleteDataProductUseCase
from backend.use_cases.data_product.get import GetDataProductUseCase
from backend.use_cases.data_product.list import ListDataProductsUseCase
from backend.use_cases.data_product.update import UpdateDataProductUseCase

logger = logging.getLogger(__name__)

router = APIRouter()


def _slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def _build_scaffold(product: DataProduct, domain_name: str) -> dict[str, str]:
    readme = (
        f"# {product.name}\n\n"
        f"{product.description}\n\n"
        f"**Domain:** {domain_name}\n\n"
        "This repository holds the implementation code (pipeline, tests, "
        "infrastructure) for the data product. The public contract YAML lives "
        "in the central contracts repository.\n\n"
        "## Layout\n\n"
        "- `pipeline/` — transformation code\n"
        "- `tests/` — pipeline and contract-conformance tests\n"
        "- `infrastructure/` — IaC for resources owned by this product\n"
    )
    return {
        "README.md": readme,
        "pipeline/.gitkeep": "",
        "tests/.gitkeep": "",
        "infrastructure/.gitkeep": "",
    }


async def _resolve_domain_name(
    contract_repo: IDataContractRepository, product: DataProduct
) -> str | None:
    contract = await contract_repo.get_by_id(product.data_contracts_id)
    return contract.domain if contract else None


async def _ensure_product_repo(
    github: GitHubClient | None,
    product: DataProduct,
    product_repo: IDataProductRepository,
    contract_repo: IDataContractRepository,
) -> None:
    if github is None or product.repo_url:
        return
    try:
        domain_name = await _resolve_domain_name(contract_repo, product)
        if not domain_name:
            return
        name = f"dp-{_slugify(domain_name)}-{_slugify(product.name)}"
        created = await github.create_product_repo(name, product.description)
        await github.push_scaffold(
            created["full_name"], _build_scaffold(product, domain_name)
        )
        await product_repo.update_repo_url(product.id, created["html_url"])
        product.repo_url = created["html_url"]
    except Exception as exc:
        logger.warning(
            "GitHub repo provision failed for product %s: %s",
            product.id,
            exc,
            exc_info=True,
        )


async def _archive_product_repo(
    github: GitHubClient | None, product: DataProduct
) -> None:
    if github is None or not product.repo_url:
        return
    try:
        parts = product.repo_url.rstrip("/").split("/")
        repo_full_name = "/".join(parts[-2:])
        await github.archive_repo(repo_full_name)
    except Exception as exc:
        logger.warning(
            "GitHub archive failed for product %s: %s",
            product.id,
            exc,
            exc_info=True,
        )


def _to_response(product: DataProduct) -> DataProductResponseModel:
    return DataProductResponseModel(
        id=product.id,
        name=product.name,
        description=product.description,
        data_contracts_id=product.data_contracts_id,
        repo_url=product.repo_url,
        created_at=product.created_at,
        updated_at=product.updated_at,
    )
```

> The existing `@router.post`, `@router.get`, etc. handlers below this point stay unchanged for this task. They are rewired in Tasks 8–11.

- [ ] **Step 2: Sanity-check the module still imports**

Run: `python -c "import backend.interface.routers.data_product"`

Expected: no error.

- [ ] **Step 3: Run the existing router tests to verify nothing regressed**

Run: `pytest tests/unit/interface/test_data_product_router.py -q`

Expected: PASS.

- [ ] **Step 4: Commit**

```bash
git add backend/interface/routers/data_product.py
git commit -m "feat: add _ensure_product_repo and scaffold helpers to product router"
```

---

## Task 8: Wire `POST /data-products` to ensure repo

**Files:**
- Modify: `backend/interface/routers/data_product.py`
- Modify: `tests/unit/interface/test_data_product_router.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/unit/interface/test_data_product_router.py`:

```python
from unittest.mock import patch as _patch  # noqa: E402

from backend.interface.dependencies import (  # noqa: E402
    get_data_contract_repository,
    get_data_product_repository,
    get_github_client,
)


class _StubContract:
    def __init__(self, domain: str = "Marketing"):
        self.domain = domain


def test_create_data_product_triggers_repo_provisioning(admin_client):
    mock_uc = AsyncMock()
    mock_uc.execute.return_value = _product(name="Attribution Model")
    mock_github = AsyncMock()
    mock_github.create_product_repo.return_value = {
        "html_url": "https://github.com/acme/dp-marketing-attribution-model",
        "full_name": "acme/dp-marketing-attribution-model",
    }
    mock_github.push_scaffold = AsyncMock()
    mock_contract_repo = AsyncMock()
    mock_contract_repo.get_by_id.return_value = _StubContract("Marketing")
    mock_product_repo = AsyncMock()

    app.dependency_overrides[get_create_data_product_use_case] = lambda: mock_uc
    app.dependency_overrides[get_github_client] = lambda: mock_github
    app.dependency_overrides[get_data_contract_repository] = lambda: mock_contract_repo
    app.dependency_overrides[get_data_product_repository] = lambda: mock_product_repo

    resp = admin_client.post(
        "/api/v1/data-products",
        json={
            "name": "Attribution Model",
            "description": "desc",
            "data_contracts_id": str(CONTRACT_ID),
        },
    )
    assert resp.status_code == 201
    mock_github.create_product_repo.assert_awaited_once()
    args, kwargs = mock_github.create_product_repo.await_args
    assert args[0] == "dp-marketing-attribution-model"
    mock_github.push_scaffold.assert_awaited_once()
    mock_product_repo.update_repo_url.assert_awaited_once()
    assert (
        resp.json()["repo_url"]
        == "https://github.com/acme/dp-marketing-attribution-model"
    )


def test_create_data_product_warns_when_github_unavailable(admin_client):
    mock_uc = AsyncMock()
    mock_uc.execute.return_value = _product()
    app.dependency_overrides[get_create_data_product_use_case] = lambda: mock_uc
    app.dependency_overrides[get_github_client] = lambda: None
    app.dependency_overrides[get_data_contract_repository] = lambda: AsyncMock()
    app.dependency_overrides[get_data_product_repository] = lambda: AsyncMock()
    resp = admin_client.post(
        "/api/v1/data-products",
        json={
            "name": "X",
            "description": "y",
            "data_contracts_id": str(CONTRACT_ID),
        },
    )
    assert resp.status_code == 201
    assert resp.json()["repo_url"] is None


def test_create_data_product_swallows_github_errors(admin_client):
    mock_uc = AsyncMock()
    mock_uc.execute.return_value = _product()
    mock_github = AsyncMock()
    mock_github.create_product_repo.side_effect = RuntimeError("boom")
    mock_contract_repo = AsyncMock()
    mock_contract_repo.get_by_id.return_value = _StubContract("Marketing")
    mock_product_repo = AsyncMock()
    app.dependency_overrides[get_create_data_product_use_case] = lambda: mock_uc
    app.dependency_overrides[get_github_client] = lambda: mock_github
    app.dependency_overrides[get_data_contract_repository] = lambda: mock_contract_repo
    app.dependency_overrides[get_data_product_repository] = lambda: mock_product_repo
    resp = admin_client.post(
        "/api/v1/data-products",
        json={"name": "X", "description": "y", "data_contracts_id": str(CONTRACT_ID)},
    )
    assert resp.status_code == 201
    assert resp.json()["repo_url"] is None
    mock_product_repo.update_repo_url.assert_not_awaited()
```

- [ ] **Step 2: Run to confirm failure**

Run: `pytest tests/unit/interface/test_data_product_router.py::test_create_data_product_triggers_repo_provisioning -q`

Expected: FAIL — `mock_github.create_product_repo.assert_awaited_once` fails because POST handler does not call it yet.

- [ ] **Step 3: Rewire the POST handler**

In `backend/interface/routers/data_product.py`, replace the `create_data_product` handler with:

```python
@router.post("/data-products", response_model=DataProductResponseModel, status_code=201)
async def create_data_product(
    body: DataProductCreateModel,
    use_case: CreateDataProductUseCase = Depends(get_create_data_product_use_case),
    product_repo: IDataProductRepository = Depends(get_data_product_repository),
    contract_repo: IDataContractRepository = Depends(get_data_contract_repository),
    github: GitHubClient | None = Depends(get_github_client),
    _: User = Depends(get_current_user),
):
    product = await use_case.execute(
        name=body.name,
        description=body.description,
        data_contracts_id=body.data_contracts_id,
    )
    await _ensure_product_repo(github, product, product_repo, contract_repo)
    return _to_response(product)
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `pytest tests/unit/interface/test_data_product_router.py -q`

Expected: PASS — all three new tests pass, and existing tests still pass (the previous `test_create_data_product` does not override `get_github_client`, so `get_github_client` returns `None` from the real dependency because `GITHUB_TOKEN` is empty in test env, and the helper returns early).

- [ ] **Step 5: Commit**

```bash
git add backend/interface/routers/data_product.py tests/unit/interface/test_data_product_router.py
git commit -m "feat: provision GitHub repo on data product creation"
```

---

## Task 9: Wire `GET /data-products/{id}` to lazy-backfill

**Files:**
- Modify: `backend/interface/routers/data_product.py`
- Modify: `tests/unit/interface/test_data_product_router.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/unit/interface/test_data_product_router.py`:

```python
def test_get_data_product_backfills_repo_when_missing(admin_client):
    mock_uc = AsyncMock()
    mock_uc.execute.return_value = _product()
    mock_github = AsyncMock()
    mock_github.create_product_repo.return_value = {
        "html_url": "https://github.com/acme/dp-marketing-orders-product",
        "full_name": "acme/dp-marketing-orders-product",
    }
    mock_github.push_scaffold = AsyncMock()
    mock_contract_repo = AsyncMock()
    mock_contract_repo.get_by_id.return_value = _StubContract("Marketing")
    mock_product_repo = AsyncMock()
    app.dependency_overrides[get_get_data_product_use_case] = lambda: mock_uc
    app.dependency_overrides[get_github_client] = lambda: mock_github
    app.dependency_overrides[get_data_contract_repository] = lambda: mock_contract_repo
    app.dependency_overrides[get_data_product_repository] = lambda: mock_product_repo
    resp = admin_client.get(f"/api/v1/data-products/{PRODUCT_ID}")
    assert resp.status_code == 200
    mock_github.create_product_repo.assert_awaited_once()
    assert (
        resp.json()["repo_url"]
        == "https://github.com/acme/dp-marketing-orders-product"
    )


def test_get_data_product_skips_backfill_when_repo_url_set(admin_client):
    p = _product()
    p.repo_url = "https://github.com/acme/dp-existing"
    mock_uc = AsyncMock()
    mock_uc.execute.return_value = p
    mock_github = AsyncMock()
    app.dependency_overrides[get_get_data_product_use_case] = lambda: mock_uc
    app.dependency_overrides[get_github_client] = lambda: mock_github
    app.dependency_overrides[get_data_contract_repository] = lambda: AsyncMock()
    app.dependency_overrides[get_data_product_repository] = lambda: AsyncMock()
    resp = admin_client.get(f"/api/v1/data-products/{PRODUCT_ID}")
    assert resp.status_code == 200
    mock_github.create_product_repo.assert_not_awaited()


def test_list_data_products_does_not_backfill(admin_client):
    mock_uc = AsyncMock()
    mock_uc.execute.return_value = [_product(), _product(id=uuid.uuid4(), name="B")]
    mock_github = AsyncMock()
    app.dependency_overrides[get_list_data_products_use_case] = lambda: mock_uc
    app.dependency_overrides[get_github_client] = lambda: mock_github
    resp = admin_client.get("/api/v1/data-products")
    assert resp.status_code == 200
    mock_github.create_product_repo.assert_not_awaited()
```

- [ ] **Step 2: Run to confirm failure**

Run: `pytest tests/unit/interface/test_data_product_router.py::test_get_data_product_backfills_repo_when_missing -q`

Expected: FAIL — `mock_github.create_product_repo.assert_awaited_once` fails.

- [ ] **Step 3: Rewire the GET-detail handler**

In `backend/interface/routers/data_product.py`, replace the `get_data_product` handler with:

```python
@router.get("/data-products/{product_id}", response_model=DataProductResponseModel)
async def get_data_product(
    product_id: uuid.UUID,
    use_case: GetDataProductUseCase = Depends(get_get_data_product_use_case),
    product_repo: IDataProductRepository = Depends(get_data_product_repository),
    contract_repo: IDataContractRepository = Depends(get_data_contract_repository),
    github: GitHubClient | None = Depends(get_github_client),
    _: User = Depends(get_current_user),
):
    product = await use_case.execute(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Data product not found")
    await _ensure_product_repo(github, product, product_repo, contract_repo)
    return _to_response(product)
```

- [ ] **Step 4: Run the tests**

Run: `pytest tests/unit/interface/test_data_product_router.py -q`

Expected: PASS for all tests including the three new ones.

- [ ] **Step 5: Commit**

```bash
git add backend/interface/routers/data_product.py tests/unit/interface/test_data_product_router.py
git commit -m "feat: lazy-backfill GitHub repo on data product detail GET"
```

---

## Task 10: Wire `PUT /data-products/{id}` to lazy-backfill

**Files:**
- Modify: `backend/interface/routers/data_product.py`
- Modify: `tests/unit/interface/test_data_product_router.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/unit/interface/test_data_product_router.py`:

```python
def test_update_data_product_backfills_repo_when_missing(admin_client):
    mock_uc = AsyncMock()
    mock_uc.execute.return_value = _product(name="Updated")
    mock_github = AsyncMock()
    mock_github.create_product_repo.return_value = {
        "html_url": "https://github.com/acme/dp-marketing-updated",
        "full_name": "acme/dp-marketing-updated",
    }
    mock_github.push_scaffold = AsyncMock()
    mock_contract_repo = AsyncMock()
    mock_contract_repo.get_by_id.return_value = _StubContract("Marketing")
    mock_product_repo = AsyncMock()
    app.dependency_overrides[get_update_data_product_use_case] = lambda: mock_uc
    app.dependency_overrides[get_github_client] = lambda: mock_github
    app.dependency_overrides[get_data_contract_repository] = lambda: mock_contract_repo
    app.dependency_overrides[get_data_product_repository] = lambda: mock_product_repo
    resp = admin_client.put(
        f"/api/v1/data-products/{PRODUCT_ID}", json={"name": "Updated"}
    )
    assert resp.status_code == 200
    mock_github.create_product_repo.assert_awaited_once()
    assert (
        resp.json()["repo_url"] == "https://github.com/acme/dp-marketing-updated"
    )
```

- [ ] **Step 2: Run to confirm failure**

Run: `pytest tests/unit/interface/test_data_product_router.py::test_update_data_product_backfills_repo_when_missing -q`

Expected: FAIL.

- [ ] **Step 3: Rewire the PUT handler**

In `backend/interface/routers/data_product.py`, replace the `update_data_product` handler with:

```python
@router.put("/data-products/{product_id}", response_model=DataProductResponseModel)
async def update_data_product(
    product_id: uuid.UUID,
    body: DataProductUpdateModel,
    use_case: UpdateDataProductUseCase = Depends(get_update_data_product_use_case),
    product_repo: IDataProductRepository = Depends(get_data_product_repository),
    contract_repo: IDataContractRepository = Depends(get_data_contract_repository),
    github: GitHubClient | None = Depends(get_github_client),
    _: User = Depends(get_current_user),
):
    product = await use_case.execute(
        product_id=product_id,
        name=body.name,
        description=body.description,
        data_contracts_id=body.data_contracts_id,
    )
    if not product:
        raise HTTPException(status_code=404, detail="Data product not found")
    await _ensure_product_repo(github, product, product_repo, contract_repo)
    return _to_response(product)
```

- [ ] **Step 4: Run the tests**

Run: `pytest tests/unit/interface/test_data_product_router.py -q`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/interface/routers/data_product.py tests/unit/interface/test_data_product_router.py
git commit -m "feat: lazy-backfill GitHub repo on data product update"
```

---

## Task 11: Wire `DELETE /data-products/{id}` to archive

**Files:**
- Modify: `backend/interface/routers/data_product.py`
- Modify: `tests/unit/interface/test_data_product_router.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/unit/interface/test_data_product_router.py`:

```python
def test_delete_data_product_archives_repo(admin_client):
    p = _product()
    p.repo_url = "https://github.com/acme/dp-marketing-orders-product"
    mock_get_uc = AsyncMock()
    mock_get_uc.execute.return_value = p
    mock_delete_uc = AsyncMock()
    mock_delete_uc.execute.return_value = True
    mock_github = AsyncMock()
    app.dependency_overrides[get_get_data_product_use_case] = lambda: mock_get_uc
    app.dependency_overrides[get_delete_data_product_use_case] = lambda: mock_delete_uc
    app.dependency_overrides[get_github_client] = lambda: mock_github
    resp = admin_client.delete(f"/api/v1/data-products/{PRODUCT_ID}")
    assert resp.status_code == 204
    mock_github.archive_repo.assert_awaited_once_with(
        "acme/dp-marketing-orders-product"
    )


def test_delete_data_product_without_repo_url_does_not_archive(admin_client):
    mock_get_uc = AsyncMock()
    mock_get_uc.execute.return_value = _product()  # repo_url=None by default
    mock_delete_uc = AsyncMock()
    mock_delete_uc.execute.return_value = True
    mock_github = AsyncMock()
    app.dependency_overrides[get_get_data_product_use_case] = lambda: mock_get_uc
    app.dependency_overrides[get_delete_data_product_use_case] = lambda: mock_delete_uc
    app.dependency_overrides[get_github_client] = lambda: mock_github
    resp = admin_client.delete(f"/api/v1/data-products/{PRODUCT_ID}")
    assert resp.status_code == 204
    mock_github.archive_repo.assert_not_awaited()
```

- [ ] **Step 2: Run to confirm failure**

Run: `pytest tests/unit/interface/test_data_product_router.py::test_delete_data_product_archives_repo -q`

Expected: FAIL — current DELETE handler never touches GitHub.

- [ ] **Step 3: Rewire the DELETE handler**

In `backend/interface/routers/data_product.py`, replace the `delete_data_product` handler with:

```python
@router.delete("/data-products/{product_id}", status_code=204)
async def delete_data_product(
    product_id: uuid.UUID,
    use_case: DeleteDataProductUseCase = Depends(get_delete_data_product_use_case),
    get_use_case: GetDataProductUseCase = Depends(get_get_data_product_use_case),
    github: GitHubClient | None = Depends(get_github_client),
    _: User = Depends(get_current_user),
):
    product = await get_use_case.execute(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Data product not found")
    deleted = await use_case.execute(product_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Data product not found")
    await _archive_product_repo(github, product)
```

- [ ] **Step 4: Run the tests**

Run: `pytest tests/unit/interface/test_data_product_router.py -q`

Expected: PASS — both new tests pass; previous `test_delete_data_product` and `test_delete_data_product_not_found` still pass.

Note: the existing `test_delete_data_product` and `test_delete_data_product_not_found` only override the delete use case. After this change they also need the get use case overridden. If either test fails, update them as follows:

- For `test_delete_data_product`, add before the `resp = admin_client.delete(...)` line:

```python
    mock_get = AsyncMock()
    mock_get.execute.return_value = _product()
    app.dependency_overrides[get_get_data_product_use_case] = lambda: mock_get
```

- For `test_delete_data_product_not_found`, add before the `resp = admin_client.delete(...)` line:

```python
    mock_get = AsyncMock()
    mock_get.execute.return_value = None
    app.dependency_overrides[get_get_data_product_use_case] = lambda: mock_get
```

Re-run after fixing.

- [ ] **Step 5: Run the full test suite as a final regression check**

Run: `pytest tests/unit/ -q`

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add backend/interface/routers/data_product.py tests/unit/interface/test_data_product_router.py
git commit -m "feat: archive GitHub repo on data product deletion"
```

---

## Final Verification

- [ ] **Step 1: Run full unit-test suite**

Run: `pytest tests/unit/ -q`

Expected: PASS.

- [ ] **Step 2: Run ruff**

Run: `ruff check backend tests`

Expected: PASS (or auto-fixable issues — accept `--fix` if needed).

- [ ] **Step 3: Spot-check the spec is fully covered**

Open `docs/superpowers/specs/2026-06-10-per-product-github-repo-design.md` and confirm:

- Migration created ✓ (Task 1)
- Entity has `repo_url` ✓ (Task 1)
- Repository SELECTs return `repo_url`; `update_repo_url` implemented ✓ (Task 2)
- Response schema includes `repo_url` ✓ (Task 3)
- `create_product_repo`, `push_scaffold`, `archive_repo` on `GitHubClient` ✓ (Tasks 4–6)
- Owner-type detection (User vs Organization) ✓ (Task 4)
- 422 adopt-on-name-already-exists path ✓ (Task 4)
- Router helper `_ensure_product_repo`, scaffold builder, warn-only logging ✓ (Task 7)
- POST triggers ensure ✓ (Task 8)
- GET detail triggers lazy backfill ✓ (Task 9)
- GET list does NOT trigger ✓ (Task 9)
- PUT triggers lazy backfill ✓ (Task 10)
- DELETE archives existing repo ✓ (Task 11)

- [ ] **Step 4: Push the branch**

```bash
git push -u origin feature/changing-to-multiples-repos
```
