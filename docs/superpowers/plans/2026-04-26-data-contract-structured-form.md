# Data Contract Structured ODCS Form — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the generic `obj: JSONB` contract model with structured ODCS core fields, a tier classification wizard, and a YAML preview on the detail page.

**Architecture:** Flat metadata columns (`title`, `version`, `owner`, `domain`, `tier`, `status`) plus two JSONB subsection columns (`models`, `servicelevels`) replace the single `obj` blob in `catalog.data_contracts`. The backend validates structure via Pydantic nested models and assembles ODCS YAML on demand from a new endpoint. The frontend replaces the textarea form with a full-page creation wizard and a structured detail view with approval actions.

**Tech Stack:** Python 3.12 / FastAPI / asyncpg / Pydantic v2 / PyYAML | TypeScript / React 18 / TanStack Query v5 / Zod / Tailwind CSS

---

## File Map

**New files:**
- `database/migrations/20260426000001_data_contract_structured.sql`
- `tests/unit/test_data_contract_entity.py`
- `tests/unit/test_data_contract_schemas.py`
- `tests/unit/test_data_contract_use_cases.py`
- `frontend/src/pages/DataContracts/TierWizard.tsx`
- `frontend/src/pages/DataContracts/ContractFields.tsx`
- `frontend/src/pages/DataContracts/NewDataContract.tsx`

**Modified files:**
- `pyproject.toml` — add pyyaml
- `database/schema/catalog.hcl` — update HCL to match new columns
- `backend/domain/entities/data_contract.py` — replace `obj` with typed fields
- `backend/domain/interfaces/data_contract_repository.py` — update method signatures
- `backend/infra/repositories/data_contract_repository.py` — rewrite SQL queries
- `backend/interface/schemas/data_contract.py` — add `SchemaField`, `ModelsSection`, `ServiceLevels`
- `backend/use_cases/data_contract/create.py` — update params
- `backend/use_cases/data_contract/update.py` — update params
- `backend/interface/routers/data_contract.py` — update `_to_response`, add YAML endpoint
- `frontend/src/types/index.ts` — update `DataContract`, add `SchemaField`
- `frontend/src/lib/api.ts` — add `getText` helper
- `frontend/src/hooks/useDataContracts.ts` — update mutations, add `useDataContractYaml`
- `frontend/src/pages/DataContracts/DataContractForm.tsx` — replace textarea with structured sections
- `frontend/src/pages/DataContracts/index.tsx` — update columns, New Contract navigates to /data-contracts/new
- `frontend/src/pages/DataContracts/DataContractDetail.tsx` — structured view + approval buttons + YAML modal
- `frontend/src/App.tsx` — add `/data-contracts/new` route

---

## Task 1: Add PyYAML dependency

**Files:**
- Modify: `pyproject.toml`

- [ ] **Step 1: Add pyyaml to project dependencies**

In `pyproject.toml`, add `pyyaml>=6.0` to the `dependencies` list so it sits alongside fastapi and asyncpg:

```toml
dependencies = [
    "setuptools==80.9.0",
    "wheel==0.45.1",
    "uvicorn[standard]>=0.23.0",
    "fastapi==0.128.0",
    "asyncpg==0.31.0",
    "python-dotenv>=1.0.0",
    "PyJWT>=2.12.1",
    "bcrypt>=5.0.0",
    "pyyaml>=6.0",
]
```

- [ ] **Step 2: Sync the virtual environment**

```bash
uv sync
```

Expected: pyyaml installed without errors.

- [ ] **Step 3: Verify import works**

```bash
python -c "import yaml; print(yaml.__version__)"
```

Expected: prints a version string (e.g. `6.0.2`).

- [ ] **Step 4: Commit**

```bash
git add pyproject.toml uv.lock
git commit -m "feat: add pyyaml dependency for ODCS YAML assembly"
```

---

## Task 2: Database migration

**Files:**
- Create: `database/migrations/20260426000001_data_contract_structured.sql`
- Modify: `database/schema/catalog.hcl`

- [ ] **Step 1: Write the migration SQL**

Create `database/migrations/20260426000001_data_contract_structured.sql`:

```sql
-- Existing contracts are dev data; clear them before changing the schema.
TRUNCATE catalog.data_products CASCADE;
TRUNCATE catalog.data_contracts CASCADE;

-- Remove the generic blob column.
ALTER TABLE catalog.data_contracts DROP COLUMN obj;

-- Add structured metadata columns.
ALTER TABLE catalog.data_contracts
    ADD COLUMN title         TEXT    NOT NULL DEFAULT '',
    ADD COLUMN version       TEXT    NOT NULL DEFAULT '1.0.0',
    ADD COLUMN owner         TEXT    NOT NULL DEFAULT '',
    ADD COLUMN domain        TEXT    NOT NULL DEFAULT '',
    ADD COLUMN tier          INT     NOT NULL DEFAULT 4
                             CONSTRAINT chk_dc_tier
                             CHECK (tier BETWEEN 1 AND 4),
    ADD COLUMN status        TEXT    NOT NULL DEFAULT 'draft'
                             CONSTRAINT chk_dc_status
                             CHECK (status IN ('draft','in_review','active','deprecated')),
    ADD COLUMN models        JSONB   NOT NULL DEFAULT '{"fields":[]}',
    ADD COLUMN servicelevels JSONB   NOT NULL DEFAULT '{"freshness":"","availability":"","retention":"","latency":""}';
```

- [ ] **Step 2: Update the Atlas HCL schema**

Replace the contents of `database/schema/catalog.hcl` with:

```hcl
# =============================================================
# Catalog Schema — Data Product Catalog
# =============================================================

schema "catalog" {}

table "data_contracts" {
  schema = schema.catalog

  column "id" {
    type    = uuid
    null    = false
    default = sql("gen_random_uuid()")
  }

  column "title" {
    type    = text
    null    = false
    default = ""
  }

  column "version" {
    type    = text
    null    = false
    default = "1.0.0"
  }

  column "owner" {
    type    = text
    null    = false
    default = ""
  }

  column "domain" {
    type    = text
    null    = false
    default = ""
  }

  column "tier" {
    type    = int
    null    = false
    default = 4
  }

  column "status" {
    type    = text
    null    = false
    default = "draft"
  }

  column "models" {
    type    = jsonb
    null    = false
    default = sql(`'{"fields":[]}'::jsonb`)
  }

  column "servicelevels" {
    type    = jsonb
    null    = false
    default = sql(`'{"freshness":"","availability":"","retention":"","latency":""}'::jsonb`)
  }

  column "created_at" {
    type    = timestamptz
    null    = false
    default = sql("now()")
  }

  column "updated_at" {
    type    = timestamptz
    null    = false
    default = sql("now()")
  }

  primary_key {
    columns = [column.id]
  }

  check "chk_dc_tier" {
    expr = "tier BETWEEN 1 AND 4"
  }

  check "chk_dc_status" {
    expr = "status IN ('draft','in_review','active','deprecated')"
  }
}

table "data_products" {
  schema = schema.catalog

  column "id" {
    type    = uuid
    null    = false
    default = sql("gen_random_uuid()")
  }

  column "name" {
    type = text
    null = false
  }

  column "description" {
    type = text
    null = false
  }

  column "data_contracts_id" {
    type = uuid
    null = false
  }

  column "created_at" {
    type    = timestamptz
    null    = false
    default = sql("now()")
  }

  column "updated_at" {
    type    = timestamptz
    null    = false
    default = sql("now()")
  }

  primary_key {
    columns = [column.id]
  }

  foreign_key "data_products_data_contracts_id_fkey" {
    columns     = [column.data_contracts_id]
    ref_columns = [table.data_contracts.column.id]
    on_update   = CASCADE
    on_delete   = RESTRICT
  }

  index "idx_data_products_contract" {
    columns = [column.data_contracts_id]
  }
}
```

- [ ] **Step 3: Regenerate the Atlas migration hash**

Run from the `database/` directory (PowerShell):

```powershell
cd database
docker run --rm `
   -v ${PWD}/migrations:/migrations `
   arigaio/atlas migrate hash `
   --dir "file:///migrations"
cd ..
```

Expected: `database/migrations/atlas.sum` is updated with the new hash for the migration file.

- [ ] **Step 4: Apply the migration**

```powershell
cd database
docker run --rm --network local-network `
   -v ${PWD}:/project `
   -w /project `
   --env-file ../.env `
   arigaio/atlas migrate apply `
   --env local
cd ..
```

Expected: migration `20260426000001_data_contract_structured` applied successfully.

- [ ] **Step 5: Commit**

```bash
git add database/migrations/20260426000001_data_contract_structured.sql database/schema/catalog.hcl database/migrations/atlas.sum
git commit -m "feat: migrate data_contracts to structured ODCS columns"
```

---

## Task 3: Backend — domain entity and repository interface

**Files:**
- Modify: `backend/domain/entities/data_contract.py`
- Modify: `backend/domain/interfaces/data_contract_repository.py`
- Create: `tests/unit/test_data_contract_entity.py`

- [ ] **Step 1: Write the failing entity test**

Create `tests/unit/test_data_contract_entity.py`:

```python
import uuid
from datetime import datetime, timezone

from backend.domain.entities.data_contract import DataContract


def test_data_contract_has_required_fields():
    now = datetime.now(tz=timezone.utc)
    contract = DataContract(
        id=uuid.uuid4(),
        title="Orders Contract",
        version="1.0.0",
        owner="data-team",
        domain="commerce",
        tier=2,
        status="draft",
        models={"fields": []},
        servicelevels={"freshness": "24h", "availability": "99.9%", "retention": "365d", "latency": "1h"},
        created_at=now,
        updated_at=now,
    )
    assert contract.title == "Orders Contract"
    assert contract.tier == 2
    assert contract.status == "draft"
    assert contract.models == {"fields": []}
```

- [ ] **Step 2: Run test — expect failure**

```bash
python -m pytest tests/unit/test_data_contract_entity.py -v
```

Expected: `FAILED` — `DataContract.__init__` doesn't accept the new params yet.

- [ ] **Step 3: Update the entity**

Replace `backend/domain/entities/data_contract.py`:

```python
import uuid
from datetime import datetime
from typing import Any


class DataContract:
    def __init__(
        self,
        id: uuid.UUID,
        title: str,
        version: str,
        owner: str,
        domain: str,
        tier: int,
        status: str,
        models: dict[str, Any],
        servicelevels: dict[str, Any],
        created_at: datetime,
        updated_at: datetime,
    ):
        self.id = id
        self.title = title
        self.version = version
        self.owner = owner
        self.domain = domain
        self.tier = tier
        self.status = status
        self.models = models
        self.servicelevels = servicelevels
        self.created_at = created_at
        self.updated_at = updated_at
```

- [ ] **Step 4: Update the repository interface**

Replace `backend/domain/interfaces/data_contract_repository.py`:

```python
import uuid
from abc import ABC, abstractmethod
from typing import Any

from backend.domain.entities.data_contract import DataContract


class IDataContractRepository(ABC):
    @abstractmethod
    async def create(
        self,
        title: str,
        version: str,
        owner: str,
        domain: str,
        tier: int,
        status: str,
        models: dict[str, Any],
        servicelevels: dict[str, Any],
    ) -> DataContract: ...

    @abstractmethod
    async def get_by_id(self, contract_id: uuid.UUID) -> DataContract | None: ...

    @abstractmethod
    async def list(self) -> list[DataContract]: ...

    @abstractmethod
    async def update(
        self,
        contract_id: uuid.UUID,
        title: str,
        version: str,
        owner: str,
        domain: str,
        tier: int,
        status: str,
        models: dict[str, Any],
        servicelevels: dict[str, Any],
    ) -> DataContract | None: ...

    @abstractmethod
    async def delete(self, contract_id: uuid.UUID) -> bool: ...
```

- [ ] **Step 5: Run test — expect pass**

```bash
python -m pytest tests/unit/test_data_contract_entity.py -v
```

Expected: `PASSED`.

- [ ] **Step 6: Commit**

```bash
git add backend/domain/entities/data_contract.py backend/domain/interfaces/data_contract_repository.py tests/unit/test_data_contract_entity.py
git commit -m "feat: update DataContract entity and repository interface for structured ODCS fields"
```

---

## Task 4: Backend — Pydantic schemas

**Files:**
- Modify: `backend/interface/schemas/data_contract.py`
- Create: `tests/unit/test_data_contract_schemas.py`

- [ ] **Step 1: Write failing schema validation tests**

Create `tests/unit/test_data_contract_schemas.py`:

```python
import pytest
from pydantic import ValidationError

from backend.interface.schemas.data_contract import DataContractCreateModel


def test_valid_create_model():
    m = DataContractCreateModel(
        title="Orders",
        owner="alice",
        domain="commerce",
        tier=2,
    )
    assert m.version == "1.0.0"
    assert m.status == "draft"
    assert m.models.fields == []


def test_tier_below_range_rejected():
    with pytest.raises(ValidationError):
        DataContractCreateModel(title="x", owner="o", domain="d", tier=0)


def test_tier_above_range_rejected():
    with pytest.raises(ValidationError):
        DataContractCreateModel(title="x", owner="o", domain="d", tier=5)


def test_invalid_status_rejected():
    with pytest.raises(ValidationError):
        DataContractCreateModel(title="x", owner="o", domain="d", tier=1, status="unknown")


def test_schema_field_defaults():
    m = DataContractCreateModel(title="x", owner="o", domain="d", tier=3)
    assert m.servicelevels.freshness == ""
    assert m.servicelevels.availability == ""
```

- [ ] **Step 2: Run tests — expect failure**

```bash
python -m pytest tests/unit/test_data_contract_schemas.py -v
```

Expected: `FAILED` — new schema classes don't exist yet.

- [ ] **Step 3: Rewrite the schemas module**

Replace `backend/interface/schemas/data_contract.py`:

```python
import uuid
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class SchemaField(BaseModel):
    name: str
    type: Literal["string", "integer", "float", "boolean", "date", "timestamp"]
    description: str = ""
    nullable: bool = True
    primary_key: bool = False


class ModelsSection(BaseModel):
    fields: list[SchemaField] = []


class ServiceLevels(BaseModel):
    freshness: str = ""
    availability: str = ""
    retention: str = ""
    latency: str = ""


class DataContractCreateModel(BaseModel):
    title: str
    version: str = "1.0.0"
    owner: str
    domain: str
    tier: int = Field(..., ge=1, le=4)
    status: Literal["draft", "in_review", "active", "deprecated"] = "draft"
    models: ModelsSection = Field(default_factory=ModelsSection)
    servicelevels: ServiceLevels = Field(default_factory=ServiceLevels)


class DataContractUpdateModel(BaseModel):
    title: str | None = None
    version: str | None = None
    owner: str | None = None
    domain: str | None = None
    tier: int | None = Field(default=None, ge=1, le=4)
    status: Literal["draft", "in_review", "active", "deprecated"] | None = None
    models: ModelsSection | None = None
    servicelevels: ServiceLevels | None = None


class DataContractResponseModel(BaseModel):
    id: uuid.UUID
    title: str
    version: str
    owner: str
    domain: str
    tier: int
    status: str
    models: dict[str, Any]
    servicelevels: dict[str, Any]
    created_at: datetime
    updated_at: datetime
```

- [ ] **Step 4: Run tests — expect pass**

```bash
python -m pytest tests/unit/test_data_contract_schemas.py -v
```

Expected: all 5 tests `PASSED`.

- [ ] **Step 5: Commit**

```bash
git add backend/interface/schemas/data_contract.py tests/unit/test_data_contract_schemas.py
git commit -m "feat: add structured ODCS Pydantic schemas with tier and status validation"
```

---

## Task 5: Backend — use cases

**Files:**
- Modify: `backend/use_cases/data_contract/create.py`
- Modify: `backend/use_cases/data_contract/update.py`
- Create: `tests/unit/test_data_contract_use_cases.py`

- [ ] **Step 1: Write failing use case tests**

Create `tests/unit/test_data_contract_use_cases.py`:

```python
import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock

import pytest

from backend.domain.entities.data_contract import DataContract
from backend.use_cases.data_contract.create import CreateDataContractUseCase
from backend.use_cases.data_contract.update import UpdateDataContractUseCase

NOW = datetime.now(tz=timezone.utc)


def make_contract(**kwargs) -> DataContract:
    defaults = dict(
        id=uuid.uuid4(),
        title="T",
        version="1.0.0",
        owner="o",
        domain="d",
        tier=3,
        status="draft",
        models={"fields": []},
        servicelevels={"freshness": "", "availability": "", "retention": "", "latency": ""},
        created_at=NOW,
        updated_at=NOW,
    )
    return DataContract(**{**defaults, **kwargs})


@pytest.mark.asyncio
async def test_create_calls_repository():
    repo = AsyncMock()
    repo.create.return_value = make_contract(title="Orders")
    use_case = CreateDataContractUseCase(repo)

    result = await use_case.execute(
        title="Orders", version="1.0.0", owner="alice", domain="commerce",
        tier=2, status="draft", models={"fields": []},
        servicelevels={"freshness": "24h", "availability": "", "retention": "", "latency": ""},
    )

    repo.create.assert_called_once()
    assert result.title == "Orders"


@pytest.mark.asyncio
async def test_create_raises_on_empty_title():
    repo = AsyncMock()
    use_case = CreateDataContractUseCase(repo)

    with pytest.raises(ValueError, match="title"):
        await use_case.execute(
            title="", version="1.0.0", owner="alice", domain="commerce",
            tier=2, status="draft", models={"fields": []},
            servicelevels={"freshness": "", "availability": "", "retention": "", "latency": ""},
        )


@pytest.mark.asyncio
async def test_update_calls_repository():
    repo = AsyncMock()
    cid = uuid.uuid4()
    repo.update.return_value = make_contract(title="Updated")
    use_case = UpdateDataContractUseCase(repo)

    result = await use_case.execute(
        contract_id=cid,
        title="Updated", version="1.0.0", owner="bob", domain="finance",
        tier=1, status="in_review", models={"fields": []},
        servicelevels={"freshness": "1h", "availability": "99.9%", "retention": "365d", "latency": "30m"},
    )

    repo.update.assert_called_once()
    assert result.title == "Updated"
```

- [ ] **Step 2: Run tests — expect failure**

```bash
python -m pytest tests/unit/test_data_contract_use_cases.py -v
```

Expected: `FAILED` — use cases still have old `obj` signatures.

- [ ] **Step 3: Update CreateDataContractUseCase**

Replace `backend/use_cases/data_contract/create.py`:

```python
from typing import Any

from backend.domain.entities.data_contract import DataContract
from backend.domain.interfaces.data_contract_repository import IDataContractRepository


class CreateDataContractUseCase:
    def __init__(self, repository: IDataContractRepository):
        self.repository = repository

    async def execute(
        self,
        title: str,
        version: str,
        owner: str,
        domain: str,
        tier: int,
        status: str,
        models: dict[str, Any],
        servicelevels: dict[str, Any],
    ) -> DataContract:
        if not title:
            raise ValueError("Data contract title cannot be empty")
        return await self.repository.create(
            title=title,
            version=version,
            owner=owner,
            domain=domain,
            tier=tier,
            status=status,
            models=models,
            servicelevels=servicelevels,
        )
```

- [ ] **Step 4: Update UpdateDataContractUseCase**

Replace `backend/use_cases/data_contract/update.py`:

```python
import uuid
from typing import Any

from backend.domain.entities.data_contract import DataContract
from backend.domain.interfaces.data_contract_repository import IDataContractRepository


class UpdateDataContractUseCase:
    def __init__(self, repository: IDataContractRepository):
        self.repository = repository

    async def execute(
        self,
        contract_id: uuid.UUID,
        title: str,
        version: str,
        owner: str,
        domain: str,
        tier: int,
        status: str,
        models: dict[str, Any],
        servicelevels: dict[str, Any],
    ) -> DataContract | None:
        if not title:
            raise ValueError("Data contract title cannot be empty")
        return await self.repository.update(
            contract_id=contract_id,
            title=title,
            version=version,
            owner=owner,
            domain=domain,
            tier=tier,
            status=status,
            models=models,
            servicelevels=servicelevels,
        )
```

- [ ] **Step 5: Run tests — expect pass**

```bash
python -m pytest tests/unit/test_data_contract_use_cases.py -v
```

Expected: all 3 tests `PASSED`.

- [ ] **Step 6: Commit**

```bash
git add backend/use_cases/data_contract/create.py backend/use_cases/data_contract/update.py tests/unit/test_data_contract_use_cases.py
git commit -m "feat: update data contract use cases for structured ODCS fields"
```

---

## Task 6: Backend — repository SQL rewrite

**Files:**
- Modify: `backend/infra/repositories/data_contract_repository.py`

- [ ] **Step 1: Rewrite the Postgres repository**

Replace the full contents of `backend/infra/repositories/data_contract_repository.py`:

```python
import json
import uuid
from typing import Any

from backend.domain.entities.data_contract import DataContract
from backend.domain.interfaces.data_contract_repository import IDataContractRepository

_SELECT = """
    SELECT id, title, version, owner, domain, tier, status,
           models, servicelevels, created_at, updated_at
    FROM catalog.data_contracts
"""


def _row_to_entity(row) -> DataContract:
    return DataContract(
        id=row["id"],
        title=row["title"],
        version=row["version"],
        owner=row["owner"],
        domain=row["domain"],
        tier=row["tier"],
        status=row["status"],
        models=json.loads(row["models"]),
        servicelevels=json.loads(row["servicelevels"]),
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


class PostgresDataContractRepository(IDataContractRepository):
    def __init__(self, db):
        self.db = db

    async def create(
        self,
        title: str,
        version: str,
        owner: str,
        domain: str,
        tier: int,
        status: str,
        models: dict[str, Any],
        servicelevels: dict[str, Any],
    ) -> DataContract:
        async with self.db.transaction():
            row = await self.db.fetchrow(
                """
                INSERT INTO catalog.data_contracts
                    (title, version, owner, domain, tier, status, models, servicelevels)
                VALUES ($1, $2, $3, $4, $5, $6, $7::jsonb, $8::jsonb)
                RETURNING id, title, version, owner, domain, tier, status,
                          models, servicelevels, created_at, updated_at;
                """,
                title, version, owner, domain, tier, status,
                json.dumps(models), json.dumps(servicelevels),
            )
            return _row_to_entity(row)

    async def get_by_id(self, contract_id: uuid.UUID) -> DataContract | None:
        row = await self.db.fetchrow(
            f"{_SELECT} WHERE id = $1;",
            contract_id,
        )
        return _row_to_entity(row) if row else None

    async def list(self) -> list[DataContract]:
        rows = await self.db.fetch(f"{_SELECT} ORDER BY created_at DESC;")
        return [_row_to_entity(r) for r in rows]

    async def update(
        self,
        contract_id: uuid.UUID,
        title: str,
        version: str,
        owner: str,
        domain: str,
        tier: int,
        status: str,
        models: dict[str, Any],
        servicelevels: dict[str, Any],
    ) -> DataContract | None:
        async with self.db.transaction():
            row = await self.db.fetchrow(
                """
                UPDATE catalog.data_contracts
                SET title = $1, version = $2, owner = $3, domain = $4,
                    tier = $5, status = $6,
                    models = $7::jsonb, servicelevels = $8::jsonb,
                    updated_at = now()
                WHERE id = $9
                RETURNING id, title, version, owner, domain, tier, status,
                          models, servicelevels, created_at, updated_at;
                """,
                title, version, owner, domain, tier, status,
                json.dumps(models), json.dumps(servicelevels),
                contract_id,
            )
            return _row_to_entity(row) if row else None

    async def delete(self, contract_id: uuid.UUID) -> bool:
        async with self.db.transaction():
            result = await self.db.execute(
                "DELETE FROM catalog.data_contracts WHERE id = $1;",
                contract_id,
            )
            return result == "DELETE 1"
```

- [ ] **Step 2: Run all existing backend tests to confirm nothing is broken**

```bash
python -m pytest tests/ -v
```

Expected: all tests pass (entity, schema, use case tests from previous tasks).

- [ ] **Step 3: Commit**

```bash
git add backend/infra/repositories/data_contract_repository.py
git commit -m "feat: rewrite data contract SQL repository for structured ODCS columns"
```

---

## Task 7: Backend — router update and YAML endpoint

**Files:**
- Modify: `backend/interface/routers/data_contract.py`

- [ ] **Step 1: Rewrite the data contract router**

Replace the full contents of `backend/interface/routers/data_contract.py`:

```python
import uuid
from typing import List

import yaml
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import PlainTextResponse

from backend.domain.entities.data_contract import DataContract
from backend.domain.entities.user import User
from backend.interface.dependencies import (
    get_create_data_contract_use_case,
    get_delete_data_contract_use_case,
    get_get_data_contract_use_case,
    get_list_data_contracts_use_case,
    get_update_data_contract_use_case,
)
from backend.interface.schemas.data_contract import (
    DataContractCreateModel,
    DataContractResponseModel,
    DataContractUpdateModel,
)
from backend.interface.security import get_current_user
from backend.use_cases.data_contract.create import CreateDataContractUseCase
from backend.use_cases.data_contract.delete import DeleteDataContractUseCase
from backend.use_cases.data_contract.get import GetDataContractUseCase
from backend.use_cases.data_contract.list import ListDataContractsUseCase
from backend.use_cases.data_contract.update import UpdateDataContractUseCase

router = APIRouter()


def _to_response(contract: DataContract) -> DataContractResponseModel:
    return DataContractResponseModel(
        id=contract.id,
        title=contract.title,
        version=contract.version,
        owner=contract.owner,
        domain=contract.domain,
        tier=contract.tier,
        status=contract.status,
        models=contract.models,
        servicelevels=contract.servicelevels,
        created_at=contract.created_at,
        updated_at=contract.updated_at,
    )


def _assemble_yaml(contract: DataContract) -> str:
    payload = {
        "dataContractSpecification": "0.9.3",
        "id": str(contract.id),
        "info": {
            "title": contract.title,
            "version": contract.version,
            "owner": contract.owner,
            "domain": contract.domain,
            "status": contract.status,
        },
        "models": contract.models,
        "servicelevels": contract.servicelevels,
        "x-tier": contract.tier,
    }
    return yaml.dump(payload, default_flow_style=False, allow_unicode=True, sort_keys=False)


@router.post("/data-contracts", response_model=DataContractResponseModel, status_code=201)
async def create_data_contract(
    body: DataContractCreateModel,
    use_case: CreateDataContractUseCase = Depends(get_create_data_contract_use_case),
    _: User = Depends(get_current_user),
):
    try:
        contract = await use_case.execute(
            title=body.title,
            version=body.version,
            owner=body.owner,
            domain=body.domain,
            tier=body.tier,
            status=body.status,
            models=body.models.model_dump(),
            servicelevels=body.servicelevels.model_dump(),
        )
        return _to_response(contract)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/data-contracts", response_model=List[DataContractResponseModel])
async def list_data_contracts(
    use_case: ListDataContractsUseCase = Depends(get_list_data_contracts_use_case),
    _: User = Depends(get_current_user),
):
    contracts = await use_case.execute()
    return [_to_response(c) for c in contracts]


@router.get("/data-contracts/{contract_id}/yaml", response_class=PlainTextResponse)
async def get_data_contract_yaml(
    contract_id: uuid.UUID,
    use_case: GetDataContractUseCase = Depends(get_get_data_contract_use_case),
    _: User = Depends(get_current_user),
):
    contract = await use_case.execute(contract_id)
    if not contract:
        raise HTTPException(status_code=404, detail="Data contract not found")
    return PlainTextResponse(_assemble_yaml(contract), media_type="text/plain")


@router.get("/data-contracts/{contract_id}", response_model=DataContractResponseModel)
async def get_data_contract(
    contract_id: uuid.UUID,
    use_case: GetDataContractUseCase = Depends(get_get_data_contract_use_case),
    _: User = Depends(get_current_user),
):
    contract = await use_case.execute(contract_id)
    if not contract:
        raise HTTPException(status_code=404, detail="Data contract not found")
    return _to_response(contract)


@router.put("/data-contracts/{contract_id}", response_model=DataContractResponseModel)
async def update_data_contract(
    contract_id: uuid.UUID,
    body: DataContractUpdateModel,
    use_case: UpdateDataContractUseCase = Depends(get_update_data_contract_use_case),
    _: User = Depends(get_current_user),
):
    existing = await GetDataContractUseCase(use_case.repository).execute(contract_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Data contract not found")

    try:
        contract = await use_case.execute(
            contract_id=contract_id,
            title=body.title if body.title is not None else existing.title,
            version=body.version if body.version is not None else existing.version,
            owner=body.owner if body.owner is not None else existing.owner,
            domain=body.domain if body.domain is not None else existing.domain,
            tier=body.tier if body.tier is not None else existing.tier,
            status=body.status if body.status is not None else existing.status,
            models=body.models.model_dump() if body.models is not None else existing.models,
            servicelevels=body.servicelevels.model_dump() if body.servicelevels is not None else existing.servicelevels,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    if not contract:
        raise HTTPException(status_code=404, detail="Data contract not found")
    return _to_response(contract)


@router.delete("/data-contracts/{contract_id}", status_code=204)
async def delete_data_contract(
    contract_id: uuid.UUID,
    use_case: DeleteDataContractUseCase = Depends(get_delete_data_contract_use_case),
    _: User = Depends(get_current_user),
):
    deleted = await use_case.execute(contract_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Data contract not found")
```

> **Note on the PUT handler:** it fetches the existing contract first to apply partial updates — only fields sent in the body overwrite the stored values. This avoids requiring a full payload on every edit.
> **Note on route order:** the `/yaml` route is declared before `/{contract_id}` so FastAPI matches it first and does not interpret `yaml` as a UUID.

- [ ] **Step 2: Run all backend tests**

```bash
python -m pytest tests/ -v
```

Expected: all tests pass.

- [ ] **Step 3: Start the server and verify the YAML endpoint manually**

```bash
uvicorn backend.main:app --reload
```

In another terminal (after creating a contract via Swagger at `http://localhost:8000/docs`):

```bash
curl -H "Authorization: Bearer <token>" http://localhost:8000/api/v1/data-contracts/<id>/yaml
```

Expected: ODCS YAML text is returned.

- [ ] **Step 4: Commit**

```bash
git add backend/interface/routers/data_contract.py
git commit -m "feat: update data contract router for structured fields and add YAML endpoint"
```

---

## Task 8: Frontend — types and API helper

**Files:**
- Modify: `frontend/src/types/index.ts`
- Modify: `frontend/src/lib/api.ts`

- [ ] **Step 1: Update TypeScript types**

Replace the `DataContract`, `DataContractFormData` entries in `frontend/src/types/index.ts`. Full new file contents:

```typescript
export interface SchemaField {
  name: string
  type: 'string' | 'integer' | 'float' | 'boolean' | 'date' | 'timestamp'
  description: string
  nullable: boolean
  primary_key: boolean
}

export interface DataContract {
  id: string
  title: string
  version: string
  owner: string
  domain: string
  tier: 1 | 2 | 3 | 4
  status: 'draft' | 'in_review' | 'active' | 'deprecated'
  models: { fields: SchemaField[] }
  servicelevels: {
    freshness: string
    availability: string
    retention: string
    latency: string
  }
  created_at: string
  updated_at: string
}

export interface DataContractInput {
  title: string
  version: string
  owner: string
  domain: string
  tier: number
  status: string
  models: { fields: SchemaField[] }
  servicelevels: {
    freshness: string
    availability: string
    retention: string
    latency: string
  }
}

export interface DataProduct {
  id: string
  name: string
  description: string
  data_contracts_id: string
  created_at: string
  updated_at: string
}

export interface User {
  id: string
  username: string
  email: string
}

export interface DataProductFormData {
  name: string
  description: string
  data_contracts_id: string
}

export interface UserFormData {
  username: string
  email: string
}
```

- [ ] **Step 2: Add getText helper to api.ts**

Add the following function at the end of `frontend/src/lib/api.ts` (after the `del` export):

```typescript
export async function getText(path: string): Promise<string> {
  const res = await fetchWithRetry(`${BASE_URL}${path}`, { method: 'GET' })
  if (!res.ok) {
    throw new ApiError(res.status, `HTTP error ${res.status}`)
  }
  return res.text()
}
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/types/index.ts frontend/src/lib/api.ts
git commit -m "feat: update DataContract TypeScript types and add getText API helper"
```

---

## Task 9: Frontend — hooks update

**Files:**
- Modify: `frontend/src/hooks/useDataContracts.ts`

- [ ] **Step 1: Rewrite the data contracts hooks**

Replace the full contents of `frontend/src/hooks/useDataContracts.ts`:

```typescript
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { get, post, put, del, getText } from '../lib/api'
import type { DataContract, DataContractInput } from '../types'

const KEYS = {
  all: ['data-contracts'] as const,
  one: (id: string) => ['data-contracts', id] as const,
  yaml: (id: string) => ['data-contracts', id, 'yaml'] as const,
}

export function useDataContracts() {
  return useQuery<DataContract[]>({
    queryKey: KEYS.all,
    queryFn: () => get<DataContract[]>('/data-contracts'),
  })
}

export function useDataContract(id: string) {
  return useQuery<DataContract>({
    queryKey: KEYS.one(id),
    queryFn: () => get<DataContract>(`/data-contracts/${id}`),
    enabled: !!id,
  })
}

export function useDataContractYaml(id: string, enabled: boolean) {
  return useQuery<string>({
    queryKey: KEYS.yaml(id),
    queryFn: () => getText(`/data-contracts/${id}/yaml`),
    enabled: !!id && enabled,
  })
}

export function useCreateDataContract() {
  const qc = useQueryClient()
  return useMutation<DataContract, Error, DataContractInput>({
    mutationFn: (input) => post<DataContract>('/data-contracts', input),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: KEYS.all })
    },
  })
}

export function useUpdateDataContract() {
  const qc = useQueryClient()
  return useMutation<DataContract, Error, { id: string } & Partial<DataContractInput>>({
    mutationFn: ({ id, ...body }) =>
      put<DataContract>(`/data-contracts/${id}`, body),
    onSuccess: (updated) => {
      qc.invalidateQueries({ queryKey: KEYS.all })
      qc.invalidateQueries({ queryKey: KEYS.one(updated.id) })
      qc.invalidateQueries({ queryKey: KEYS.yaml(updated.id) })
    },
  })
}

export function useDeleteDataContract() {
  const qc = useQueryClient()
  return useMutation<void, Error, string>({
    mutationFn: (id) => del(`/data-contracts/${id}`),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: KEYS.all })
    },
  })
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/hooks/useDataContracts.ts
git commit -m "feat: update data contract hooks for structured fields and YAML query"
```

---

## Task 10: Frontend — TierWizard component

**Files:**
- Create: `frontend/src/pages/DataContracts/TierWizard.tsx`

- [ ] **Step 1: Create the TierWizard component**

Create `frontend/src/pages/DataContracts/TierWizard.tsx`:

```typescript
import { useState } from 'react'
import Button from '../../components/ui/Button'

const TIER_LABELS: Record<number, { name: string; description: string; color: string }> = {
  1: { name: 'Critical / Regulated', description: 'Errors can cause legal, regulatory, or material financial consequences.', color: 'text-red-600 dark:text-red-400' },
  2: { name: 'Business Important', description: 'Errors can lead to wrong business decisions with measurable financial impact.', color: 'text-orange-600 dark:text-orange-400' },
  3: { name: 'Operational / Internal', description: 'Errors are manageable informally with no material damage.', color: 'text-blue-600 dark:text-blue-400' },
  4: { name: 'Experimental / Sandbox', description: 'Exploration or hypothesis validation. No production consumers allowed.', color: 'text-gray-600 dark:text-gray-400' },
}

const QUESTIONS = [
  'Could an error in this data cause a regulatory, legal, or financial consequence?',
  'Could an error lead to a wrong business decision with measurable financial impact?',
  'Is the impact of an error manageable informally, with no material damage?',
]

interface TierWizardProps {
  value: number
  onChange: (tier: number) => void
}

export default function TierWizard({ value, onChange }: TierWizardProps) {
  const [step, setStep] = useState(0)
  const [done, setDone] = useState(false)

  const handleAnswer = (yes: boolean) => {
    const assignedTier = step + 1
    if (yes) {
      onChange(assignedTier)
      setDone(true)
      return
    }
    if (step < QUESTIONS.length - 1) {
      setStep(step + 1)
    } else {
      onChange(4)
      setDone(true)
    }
  }

  const reset = () => {
    setStep(0)
    setDone(false)
  }

  const tier = TIER_LABELS[value]

  return (
    <div className="rounded-lg border border-gray-200 dark:border-slate-700 p-4 space-y-4">
      <h3 className="text-sm font-semibold text-gray-700 dark:text-slate-200">
        Step 1 — Classify the Tier
      </h3>

      {!done ? (
        <div className="space-y-3">
          <p className="text-sm text-gray-600 dark:text-slate-300">
            {QUESTIONS[step]}
          </p>
          <div className="flex gap-2">
            <Button size="sm" onClick={() => handleAnswer(true)}>Yes</Button>
            <Button size="sm" variant="secondary" onClick={() => handleAnswer(false)}>No</Button>
          </div>
        </div>
      ) : (
        <div className="space-y-3">
          <div>
            <span className={`text-sm font-semibold ${tier.color}`}>
              Tier {value} — {tier.name}
            </span>
            <p className="text-xs text-gray-500 dark:text-slate-400 mt-1">{tier.description}</p>
          </div>
          <div className="flex items-center gap-3">
            <label className="text-xs text-gray-500 dark:text-slate-400">Override:</label>
            <select
              value={value}
              onChange={(e) => onChange(Number(e.target.value))}
              className="text-sm border border-gray-300 dark:border-slate-600 rounded px-2 py-1 bg-white dark:bg-slate-800 text-gray-700 dark:text-slate-200"
            >
              {[1, 2, 3, 4].map((t) => (
                <option key={t} value={t}>
                  Tier {t} — {TIER_LABELS[t].name}
                </option>
              ))}
            </select>
            <button
              onClick={reset}
              className="text-xs text-blue-600 dark:text-blue-400 hover:underline"
            >
              Restart
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/pages/DataContracts/TierWizard.tsx
git commit -m "feat: add TierWizard component with sequential yes/no questions"
```

---

## Task 11: Frontend — ContractFields component (dynamic schema builder)

**Files:**
- Create: `frontend/src/pages/DataContracts/ContractFields.tsx`

- [ ] **Step 1: Create the ContractFields component**

Create `frontend/src/pages/DataContracts/ContractFields.tsx`:

```typescript
import { Plus, Trash2 } from 'lucide-react'
import type { SchemaField } from '../../types'

const FIELD_TYPES = ['string', 'integer', 'float', 'boolean', 'date', 'timestamp'] as const

interface ContractFieldsProps {
  fields: SchemaField[]
  onChange: (fields: SchemaField[]) => void
}

const emptyField = (): SchemaField => ({
  name: '',
  type: 'string',
  description: '',
  nullable: true,
  primary_key: false,
})

export default function ContractFields({ fields, onChange }: ContractFieldsProps) {
  const update = (index: number, patch: Partial<SchemaField>) => {
    const next = fields.map((f, i) => (i === index ? { ...f, ...patch } : f))
    onChange(next)
  }

  const add = () => onChange([...fields, emptyField()])

  const remove = (index: number) => onChange(fields.filter((_, i) => i !== index))

  return (
    <div className="space-y-3">
      {fields.length === 0 && (
        <p className="text-sm text-gray-400 dark:text-slate-500 italic">No fields yet.</p>
      )}
      {fields.map((field, i) => (
        <div
          key={i}
          className="grid grid-cols-12 gap-2 items-center rounded border border-gray-200 dark:border-slate-700 p-2 bg-gray-50 dark:bg-slate-900"
        >
          {/* Name */}
          <input
            className="col-span-3 text-sm border border-gray-300 dark:border-slate-600 rounded px-2 py-1 bg-white dark:bg-slate-800 text-gray-800 dark:text-slate-200"
            placeholder="field_name"
            value={field.name}
            onChange={(e) => update(i, { name: e.target.value })}
          />
          {/* Type */}
          <select
            className="col-span-2 text-sm border border-gray-300 dark:border-slate-600 rounded px-2 py-1 bg-white dark:bg-slate-800 text-gray-800 dark:text-slate-200"
            value={field.type}
            onChange={(e) => update(i, { type: e.target.value as SchemaField['type'] })}
          >
            {FIELD_TYPES.map((t) => (
              <option key={t} value={t}>{t}</option>
            ))}
          </select>
          {/* Description */}
          <input
            className="col-span-4 text-sm border border-gray-300 dark:border-slate-600 rounded px-2 py-1 bg-white dark:bg-slate-800 text-gray-800 dark:text-slate-200"
            placeholder="Description"
            value={field.description}
            onChange={(e) => update(i, { description: e.target.value })}
          />
          {/* Nullable toggle */}
          <label className="col-span-1 flex items-center gap-1 text-xs text-gray-500 dark:text-slate-400 cursor-pointer">
            <input
              type="checkbox"
              checked={field.nullable}
              onChange={(e) => update(i, { nullable: e.target.checked })}
            />
            Null
          </label>
          {/* PK toggle */}
          <label className="col-span-1 flex items-center gap-1 text-xs text-gray-500 dark:text-slate-400 cursor-pointer">
            <input
              type="checkbox"
              checked={field.primary_key}
              onChange={(e) => update(i, { primary_key: e.target.checked })}
            />
            PK
          </label>
          {/* Remove */}
          <button
            type="button"
            onClick={() => remove(i)}
            className="col-span-1 flex items-center justify-center text-red-400 hover:text-red-600"
            title="Remove field"
          >
            <Trash2 size={14} />
          </button>
        </div>
      ))}
      <button
        type="button"
        onClick={add}
        className="flex items-center gap-1 text-sm text-blue-600 dark:text-blue-400 hover:underline"
      >
        <Plus size={14} />
        Add field
      </button>
    </div>
  )
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/pages/DataContracts/ContractFields.tsx
git commit -m "feat: add ContractFields dynamic schema field builder component"
```

---

## Task 12: Frontend — DataContractForm (structured sections)

**Files:**
- Modify: `frontend/src/pages/DataContracts/DataContractForm.tsx`

- [ ] **Step 1: Replace DataContractForm with structured sections**

Replace the full contents of `frontend/src/pages/DataContracts/DataContractForm.tsx`:

```typescript
import { useState } from 'react'
import { useForm, Controller } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import Button from '../../components/ui/Button'
import { Input } from '../../components/ui/Input'
import TierWizard from './TierWizard'
import ContractFields from './ContractFields'
import type { DataContract, DataContractInput, SchemaField } from '../../types'

const schema = z.object({
  title: z.string().min(1, 'Title is required'),
  version: z.string().min(1, 'Version is required'),
  owner: z.string().min(1, 'Owner is required'),
  domain: z.string().min(1, 'Domain is required'),
  tier: z.number().int().min(1).max(4),
  status: z.enum(['draft', 'in_review', 'active', 'deprecated']),
  freshness: z.string(),
  availability: z.string(),
  retention: z.string(),
  latency: z.string(),
})

type FormValues = z.infer<typeof schema>

interface DataContractFormProps {
  defaultValues?: DataContract
  onSubmit: (input: DataContractInput) => void
  onCancel: () => void
  isSubmitting: boolean
  showWizard?: boolean
}

export default function DataContractForm({
  defaultValues,
  onSubmit,
  onCancel,
  isSubmitting,
  showWizard = false,
}: DataContractFormProps) {
  const [fields, setFields] = useState<SchemaField[]>(
    defaultValues?.models?.fields ?? []
  )

  const {
    register,
    handleSubmit,
    control,
    formState: { errors },
  } = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      title: defaultValues?.title ?? '',
      version: defaultValues?.version ?? '1.0.0',
      owner: defaultValues?.owner ?? '',
      domain: defaultValues?.domain ?? '',
      tier: defaultValues?.tier ?? 4,
      status: defaultValues?.status ?? 'draft',
      freshness: defaultValues?.servicelevels?.freshness ?? '',
      availability: defaultValues?.servicelevels?.availability ?? '',
      retention: defaultValues?.servicelevels?.retention ?? '',
      latency: defaultValues?.servicelevels?.latency ?? '',
    },
  })

  const handleFormSubmit = (values: FormValues) => {
    onSubmit({
      title: values.title,
      version: values.version,
      owner: values.owner,
      domain: values.domain,
      tier: values.tier,
      status: values.status,
      models: { fields },
      servicelevels: {
        freshness: values.freshness,
        availability: values.availability,
        retention: values.retention,
        latency: values.latency,
      },
    })
  }

  return (
    <form onSubmit={handleSubmit(handleFormSubmit)} className="space-y-6">
      {/* Step 1 — Tier Wizard (only on creation page) */}
      {showWizard && (
        <Controller
          name="tier"
          control={control}
          render={({ field }) => (
            <TierWizard value={field.value} onChange={field.onChange} />
          )}
        />
      )}

      {/* Step 2 — Contract Info */}
      <div className="space-y-3">
        <h3 className="text-sm font-semibold text-gray-700 dark:text-slate-200">
          {showWizard ? 'Step 2 — Contract Info' : 'Contract Info'}
        </h3>
        <div className="grid grid-cols-2 gap-3">
          <Input
            label="Title"
            error={errors.title?.message}
            {...register('title')}
          />
          <Input
            label="Version"
            error={errors.version?.message}
            {...register('version')}
          />
          <Input
            label="Owner"
            error={errors.owner?.message}
            {...register('owner')}
          />
          <Input
            label="Domain"
            error={errors.domain?.message}
            {...register('domain')}
          />
        </div>
        <div className="grid grid-cols-2 gap-3">
          {!showWizard && (
            <div>
              <label className="block text-xs font-medium text-gray-600 dark:text-slate-400 mb-1">
                Tier
              </label>
              <select
                className="w-full text-sm border border-gray-300 dark:border-slate-600 rounded-lg px-3 py-2 bg-white dark:bg-slate-800 text-gray-800 dark:text-slate-200"
                {...register('tier', { valueAsNumber: true })}
              >
                <option value={1}>Tier 1 — Critical / Regulated</option>
                <option value={2}>Tier 2 — Business Important</option>
                <option value={3}>Tier 3 — Operational / Internal</option>
                <option value={4}>Tier 4 — Experimental / Sandbox</option>
              </select>
            </div>
          )}
          <div>
            <label className="block text-xs font-medium text-gray-600 dark:text-slate-400 mb-1">
              Status
            </label>
            <select
              className="w-full text-sm border border-gray-300 dark:border-slate-600 rounded-lg px-3 py-2 bg-white dark:bg-slate-800 text-gray-800 dark:text-slate-200"
              {...register('status')}
            >
              <option value="draft">Draft</option>
              <option value="in_review">In Review</option>
              <option value="active">Active</option>
              <option value="deprecated">Deprecated</option>
            </select>
          </div>
        </div>
      </div>

      {/* Step 3 — Models */}
      <div className="space-y-3">
        <h3 className="text-sm font-semibold text-gray-700 dark:text-slate-200">
          {showWizard ? 'Step 3 — Schema Fields' : 'Schema Fields'}
        </h3>
        <ContractFields fields={fields} onChange={setFields} />
      </div>

      {/* Step 4 — Service Levels */}
      <div className="space-y-3">
        <h3 className="text-sm font-semibold text-gray-700 dark:text-slate-200">
          {showWizard ? 'Step 4 — Service Levels' : 'Service Levels'}
        </h3>
        <div className="grid grid-cols-2 gap-3">
          <Input label="Freshness" placeholder="e.g. 24h" {...register('freshness')} />
          <Input label="Availability" placeholder="e.g. 99.9%" {...register('availability')} />
          <Input label="Retention" placeholder="e.g. 365d" {...register('retention')} />
          <Input label="Latency" placeholder="e.g. 1h" {...register('latency')} />
        </div>
      </div>

      <div className="flex justify-end gap-3 pt-2 border-t border-gray-200 dark:border-slate-700">
        <Button type="button" variant="secondary" onClick={onCancel}>
          Cancel
        </Button>
        <Button type="submit" loading={isSubmitting}>
          {defaultValues ? 'Save Changes' : 'Create Contract'}
        </Button>
      </div>
    </form>
  )
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/pages/DataContracts/DataContractForm.tsx
git commit -m "feat: replace DataContractForm textarea with structured ODCS sections"
```

---

## Task 13: Frontend — NewDataContract page and App route

**Files:**
- Create: `frontend/src/pages/DataContracts/NewDataContract.tsx`
- Modify: `frontend/src/App.tsx`

- [ ] **Step 1: Create the NewDataContract page**

Create `frontend/src/pages/DataContracts/NewDataContract.tsx`:

```typescript
import { useNavigate } from 'react-router-dom'
import { useCreateDataContract } from '../../hooks/useDataContracts'
import PageHeader from '../../components/PageHeader'
import Card from '../../components/ui/Card'
import DataContractForm from './DataContractForm'
import type { DataContractInput } from '../../types'

export default function NewDataContract() {
  const navigate = useNavigate()
  const createMutation = useCreateDataContract()

  const handleSubmit = async (input: DataContractInput) => {
    const created = await createMutation.mutateAsync(input)
    navigate(`/data-contracts/${created.id}`)
  }

  return (
    <div>
      <PageHeader
        title="New Data Contract"
        subtitle="Define a new ODCS-compliant contract for your data product."
        backTo="/data-contracts"
      />
      <Card>
        <DataContractForm
          onSubmit={handleSubmit}
          onCancel={() => navigate('/data-contracts')}
          isSubmitting={createMutation.isPending}
          showWizard
        />
        {createMutation.isError && (
          <p className="mt-3 text-sm text-red-500">{createMutation.error.message}</p>
        )}
      </Card>
    </div>
  )
}
```

- [ ] **Step 2: Add the new route to App.tsx**

In `frontend/src/App.tsx`, import `NewDataContract` and add the route. Replace the file contents:

```typescript
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider } from './contexts/AuthContext'
import PrivateRoute from './components/PrivateRoute'
import Layout from './components/Layout'
import Login from './pages/Login'
import Dashboard from './pages/Dashboard'
import DataContractsList from './pages/DataContracts'
import DataContractDetail from './pages/DataContracts/DataContractDetail'
import NewDataContract from './pages/DataContracts/NewDataContract'
import DataProductsList from './pages/DataProducts'
import DataProductDetail from './pages/DataProducts/DataProductDetail'
import UsersList from './pages/Users'

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route element={<PrivateRoute />}>
            <Route path="/" element={<Layout />}>
              <Route index element={<Navigate to="/dashboard" replace />} />
              <Route path="dashboard" element={<Dashboard />} />
              <Route path="data-contracts" element={<DataContractsList />} />
              <Route path="data-contracts/new" element={<NewDataContract />} />
              <Route path="data-contracts/:id" element={<DataContractDetail />} />
              <Route path="data-products" element={<DataProductsList />} />
              <Route path="data-products/:id" element={<DataProductDetail />} />
              <Route path="users" element={<UsersList />} />
            </Route>
          </Route>
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  )
}
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/pages/DataContracts/NewDataContract.tsx frontend/src/App.tsx
git commit -m "feat: add NewDataContract page and /data-contracts/new route"
```

---

## Task 14: Frontend — list page update

**Files:**
- Modify: `frontend/src/pages/DataContracts/index.tsx`

- [ ] **Step 1: Update the list page**

Replace the full contents of `frontend/src/pages/DataContracts/index.tsx`:

```typescript
import { useNavigate } from 'react-router-dom'
import { Plus, FileText, Trash2 } from 'lucide-react'
import {
  useDataContracts,
  useDeleteDataContract,
} from '../../hooks/useDataContracts'
import PageHeader from '../../components/PageHeader'
import Table from '../../components/ui/Table'
import Button from '../../components/ui/Button'
import Badge from '../../components/ui/Badge'
import Modal from '../../components/ui/Modal'
import Spinner from '../../components/ui/Spinner'
import { useState } from 'react'
import type { DataContract } from '../../types'

const TIER_COLORS: Record<number, 'red' | 'yellow' | 'blue' | 'gray'> = {
  1: 'red',
  2: 'yellow',
  3: 'blue',
  4: 'gray',
}

const STATUS_COLORS: Record<string, 'gray' | 'yellow' | 'green' | 'red'> = {
  draft: 'gray',
  in_review: 'yellow',
  active: 'green',
  deprecated: 'red',
}

function formatDate(iso: string) {
  return new Date(iso).toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  })
}

export default function DataContractsList() {
  const navigate = useNavigate()
  const [deleteTarget, setDeleteTarget] = useState<DataContract | null>(null)

  const { data: contracts = [], isLoading, error } = useDataContracts()
  const deleteMutation = useDeleteDataContract()

  const handleDelete = async () => {
    if (!deleteTarget) return
    await deleteMutation.mutateAsync(deleteTarget.id)
    setDeleteTarget(null)
  }

  const columns = [
    {
      key: 'title',
      header: 'Title',
      render: (row: DataContract) => (
        <span className="font-medium text-gray-800 dark:text-slate-200">{row.title}</span>
      ),
    },
    {
      key: 'tier',
      header: 'Tier',
      render: (row: DataContract) => (
        <Badge variant={TIER_COLORS[row.tier]}>Tier {row.tier}</Badge>
      ),
      className: 'w-24',
    },
    {
      key: 'status',
      header: 'Status',
      render: (row: DataContract) => (
        <Badge variant={STATUS_COLORS[row.status] ?? 'gray'}>
          {row.status.replace('_', ' ')}
        </Badge>
      ),
      className: 'w-28',
    },
    {
      key: 'domain',
      header: 'Domain',
      render: (row: DataContract) => (
        <span className="text-sm text-gray-600 dark:text-slate-300">{row.domain}</span>
      ),
    },
    {
      key: 'created_at',
      header: 'Created',
      render: (row: DataContract) => (
        <span className="text-sm text-gray-500 dark:text-slate-400">{formatDate(row.created_at)}</span>
      ),
    },
    {
      key: 'actions',
      header: '',
      render: (row: DataContract) => (
        <button
          onClick={(e) => { e.stopPropagation(); setDeleteTarget(row) }}
          className="btn-danger"
          title="Delete"
        >
          <Trash2 size={13} />
          Delete
        </button>
      ),
      className: 'w-24',
    },
  ]

  return (
    <div>
      <PageHeader
        title="Data Contracts"
        subtitle={`${contracts.length} contract${contracts.length !== 1 ? 's' : ''}`}
        actions={
          <Button onClick={() => navigate('/data-contracts/new')}>
            <Plus size={16} />
            New Contract
          </Button>
        }
      />

      {isLoading ? (
        <div className="flex justify-center py-20"><Spinner size="lg" /></div>
      ) : error ? (
        <div className="text-center py-16">
          <p className="text-red-500">{error.message}</p>
        </div>
      ) : contracts.length === 0 ? (
        <div className="text-center py-20">
          <FileText size={48} className="text-gray-200 dark:text-slate-700 mx-auto mb-4" />
          <p className="text-gray-500 dark:text-slate-400 font-medium mb-1">No data contracts yet</p>
          <p className="text-sm text-gray-400 dark:text-slate-500 mb-4">
            Create your first contract to get started.
          </p>
          <Button onClick={() => navigate('/data-contracts/new')}>
            <Plus size={16} />
            New Contract
          </Button>
        </div>
      ) : (
        <Table
          columns={columns}
          data={contracts}
          keyExtractor={(c) => c.id}
          onRowClick={(c) => navigate(`/data-contracts/${c.id}`)}
          emptyMessage="No contracts found."
          mobileCardConfig={{ titleKey: 'title', badgeKey: 'status' }}
        />
      )}

      <Modal
        open={!!deleteTarget}
        onClose={() => setDeleteTarget(null)}
        title="Delete Data Contract"
        size="sm"
      >
        <p className="text-sm text-gray-600 dark:text-slate-300 mb-2">
          Are you sure you want to delete{' '}
          <span className="font-medium">{deleteTarget?.title}</span>?
        </p>
        <p className="text-xs text-gray-400 dark:text-slate-500 mb-6">This action cannot be undone.</p>
        <div className="flex justify-end gap-3">
          <Button variant="secondary" onClick={() => setDeleteTarget(null)}>Cancel</Button>
          <Button variant="danger" loading={deleteMutation.isPending} onClick={handleDelete}>
            Delete
          </Button>
        </div>
        {deleteMutation.isError && (
          <p className="mt-3 text-sm text-red-500">{deleteMutation.error.message}</p>
        )}
      </Modal>
    </div>
  )
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/pages/DataContracts/index.tsx
git commit -m "feat: update data contracts list page with tier and status badges"
```

---

## Task 15: Frontend — detail page update

**Files:**
- Modify: `frontend/src/pages/DataContracts/DataContractDetail.tsx`

- [ ] **Step 1: Rewrite the detail page**

Replace the full contents of `frontend/src/pages/DataContracts/DataContractDetail.tsx`:

```typescript
import { useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { Edit2, Trash2, Calendar, Clock, FileCode } from 'lucide-react'
import {
  useDataContract,
  useUpdateDataContract,
  useDeleteDataContract,
  useDataContractYaml,
} from '../../hooks/useDataContracts'
import PageHeader from '../../components/PageHeader'
import Card from '../../components/ui/Card'
import Button from '../../components/ui/Button'
import Badge from '../../components/ui/Badge'
import Modal from '../../components/ui/Modal'
import Spinner from '../../components/ui/Spinner'
import DataContractForm from './DataContractForm'
import type { DataContractInput } from '../../types'

const TIER_COLORS: Record<number, 'red' | 'yellow' | 'blue' | 'gray'> = {
  1: 'red', 2: 'yellow', 3: 'blue', 4: 'gray',
}
const TIER_NAMES: Record<number, string> = {
  1: 'Critical / Regulated', 2: 'Business Important',
  3: 'Operational / Internal', 4: 'Experimental / Sandbox',
}
const STATUS_COLORS: Record<string, 'gray' | 'yellow' | 'green' | 'red'> = {
  draft: 'gray', in_review: 'yellow', active: 'green', deprecated: 'red',
}

function formatDateTime(iso: string) {
  return new Date(iso).toLocaleString('en-US', {
    month: 'short', day: 'numeric', year: 'numeric', hour: '2-digit', minute: '2-digit',
  })
}

export default function DataContractDetail() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [editOpen, setEditOpen] = useState(false)
  const [deleteConfirm, setDeleteConfirm] = useState(false)
  const [yamlOpen, setYamlOpen] = useState(false)

  const { data: contract, isLoading, error } = useDataContract(id ?? '')
  const updateMutation = useUpdateDataContract()
  const deleteMutation = useDeleteDataContract()
  const { data: yamlContent, isFetching: yamlLoading } = useDataContractYaml(id ?? '', yamlOpen)

  const handleUpdate = async (input: DataContractInput) => {
    if (!id) return
    await updateMutation.mutateAsync({ id, ...input })
    setEditOpen(false)
  }

  const handleDelete = async () => {
    if (!id) return
    await deleteMutation.mutateAsync(id)
    navigate('/data-contracts')
  }

  const handleApprove = () => {
    if (!id || !contract) return
    updateMutation.mutate({ id, status: 'active' })
  }

  const handleRequestChanges = () => {
    if (!id || !contract) return
    updateMutation.mutate({ id, status: 'draft' })
  }

  if (isLoading) {
    return <div className="flex items-center justify-center h-64"><Spinner size="lg" /></div>
  }

  if (error || !contract) {
    return (
      <div className="text-center py-16">
        <p className="text-red-500 font-medium">{error?.message ?? 'Contract not found'}</p>
        <button onClick={() => navigate('/data-contracts')}
          className="mt-3 text-sm text-blue-600 dark:text-blue-400 hover:underline">
          Back to list
        </button>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title={contract.title}
        subtitle={`v${contract.version} · ${contract.domain}`}
        backTo="/data-contracts"
        actions={
          <>
            <Button variant="secondary" size="sm" onClick={() => setYamlOpen(true)}>
              <FileCode size={14} />
              View YAML
            </Button>
            <Button variant="secondary" size="sm" onClick={() => setEditOpen(true)}>
              <Edit2 size={14} />
              Edit
            </Button>
            <Button variant="danger" size="sm" onClick={() => setDeleteConfirm(true)}>
              <Trash2 size={14} />
              Delete
            </Button>
          </>
        }
      />

      {/* Approval actions — only when in_review */}
      {contract.status === 'in_review' && (
        <div className="flex items-center gap-3 p-3 rounded-lg border border-yellow-200 bg-yellow-50 dark:border-yellow-700 dark:bg-yellow-900/20">
          <p className="text-sm text-yellow-800 dark:text-yellow-300 flex-1">
            This contract is awaiting review.
          </p>
          <Button size="sm" onClick={handleApprove} loading={updateMutation.isPending}>
            Approve
          </Button>
          <Button size="sm" variant="secondary" onClick={handleRequestChanges}
            loading={updateMutation.isPending}>
            Request Changes
          </Button>
        </div>
      )}

      {/* Metadata badges */}
      <div className="flex flex-wrap gap-2">
        <Badge variant={TIER_COLORS[contract.tier]}>
          Tier {contract.tier} — {TIER_NAMES[contract.tier]}
        </Badge>
        <Badge variant={STATUS_COLORS[contract.status] ?? 'gray'}>
          {contract.status.replace('_', ' ')}
        </Badge>
        <Badge variant="gray">
          <Calendar size={11} className="mr-1" />
          Created {formatDateTime(contract.created_at)}
        </Badge>
        <Badge variant="gray">
          <Clock size={11} className="mr-1" />
          Updated {formatDateTime(contract.updated_at)}
        </Badge>
      </div>

      {/* Info card */}
      <Card>
        <h2 className="text-sm font-semibold text-gray-700 dark:text-slate-200 mb-3">Info</h2>
        <dl className="grid grid-cols-2 gap-x-6 gap-y-2 text-sm">
          <div><dt className="text-gray-400 dark:text-slate-500">Owner</dt><dd className="text-gray-800 dark:text-slate-200">{contract.owner}</dd></div>
          <div><dt className="text-gray-400 dark:text-slate-500">Domain</dt><dd className="text-gray-800 dark:text-slate-200">{contract.domain}</dd></div>
          <div><dt className="text-gray-400 dark:text-slate-500">Version</dt><dd className="text-gray-800 dark:text-slate-200">{contract.version}</dd></div>
          <div><dt className="text-gray-400 dark:text-slate-500">Status</dt><dd className="text-gray-800 dark:text-slate-200">{contract.status.replace('_', ' ')}</dd></div>
        </dl>
      </Card>

      {/* Models table */}
      <Card>
        <h2 className="text-sm font-semibold text-gray-700 dark:text-slate-200 mb-3">
          Schema Fields ({contract.models.fields.length})
        </h2>
        {contract.models.fields.length === 0 ? (
          <p className="text-sm text-gray-400 dark:text-slate-500 italic">No fields defined.</p>
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-xs text-gray-400 dark:text-slate-500 border-b border-gray-200 dark:border-slate-700">
                <th className="pb-2 pr-4">Field</th>
                <th className="pb-2 pr-4">Type</th>
                <th className="pb-2 pr-4">Nullable</th>
                <th className="pb-2 pr-4">PK</th>
                <th className="pb-2">Description</th>
              </tr>
            </thead>
            <tbody>
              {contract.models.fields.map((f, i) => (
                <tr key={i} className="border-b border-gray-100 dark:border-slate-800 last:border-0">
                  <td className="py-2 pr-4 font-mono text-gray-800 dark:text-slate-200">{f.name}</td>
                  <td className="py-2 pr-4 text-gray-600 dark:text-slate-300">{f.type}</td>
                  <td className="py-2 pr-4 text-gray-500 dark:text-slate-400">{f.nullable ? 'yes' : 'no'}</td>
                  <td className="py-2 pr-4 text-gray-500 dark:text-slate-400">{f.primary_key ? '✓' : '—'}</td>
                  <td className="py-2 text-gray-500 dark:text-slate-400">{f.description || '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </Card>

      {/* Service Levels card */}
      <Card>
        <h2 className="text-sm font-semibold text-gray-700 dark:text-slate-200 mb-3">Service Levels</h2>
        <dl className="grid grid-cols-2 gap-x-6 gap-y-2 text-sm">
          <div><dt className="text-gray-400 dark:text-slate-500">Freshness</dt><dd className="text-gray-800 dark:text-slate-200">{contract.servicelevels.freshness || '—'}</dd></div>
          <div><dt className="text-gray-400 dark:text-slate-500">Availability</dt><dd className="text-gray-800 dark:text-slate-200">{contract.servicelevels.availability || '—'}</dd></div>
          <div><dt className="text-gray-400 dark:text-slate-500">Retention</dt><dd className="text-gray-800 dark:text-slate-200">{contract.servicelevels.retention || '—'}</dd></div>
          <div><dt className="text-gray-400 dark:text-slate-500">Latency</dt><dd className="text-gray-400 dark:text-slate-500">{contract.servicelevels.latency || '—'}</dd></div>
        </dl>
      </Card>

      {/* YAML Modal */}
      <Modal open={yamlOpen} onClose={() => setYamlOpen(false)} title="ODCS YAML" size="lg">
        {yamlLoading ? (
          <div className="flex justify-center py-8"><Spinner /></div>
        ) : (
          <pre className="bg-gray-50 dark:bg-slate-900 border border-gray-200 dark:border-slate-700 rounded-lg p-4 text-xs font-mono text-gray-700 dark:text-slate-300 overflow-x-auto whitespace-pre-wrap">
            {yamlContent}
          </pre>
        )}
      </Modal>

      {/* Edit Modal */}
      <Modal open={editOpen} onClose={() => setEditOpen(false)} title="Edit Data Contract" size="lg">
        <DataContractForm
          defaultValues={contract}
          onSubmit={handleUpdate}
          onCancel={() => setEditOpen(false)}
          isSubmitting={updateMutation.isPending}
        />
        {updateMutation.isError && (
          <p className="mt-3 text-sm text-red-500">{updateMutation.error.message}</p>
        )}
      </Modal>

      {/* Delete Modal */}
      <Modal open={deleteConfirm} onClose={() => setDeleteConfirm(false)} title="Delete Data Contract" size="sm">
        <p className="text-sm text-gray-600 dark:text-slate-300 mb-6">
          Are you sure you want to delete <span className="font-medium">{contract.title}</span>? This cannot be undone.
        </p>
        <div className="flex justify-end gap-3">
          <Button variant="secondary" onClick={() => setDeleteConfirm(false)}>Cancel</Button>
          <Button variant="danger" loading={deleteMutation.isPending} onClick={handleDelete}>Delete</Button>
        </div>
        {deleteMutation.isError && (
          <p className="mt-3 text-sm text-red-500">{deleteMutation.error.message}</p>
        )}
      </Modal>
    </div>
  )
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/pages/DataContracts/DataContractDetail.tsx
git commit -m "feat: rewrite DataContractDetail with structured view, YAML preview, and approval actions"
```

---

## Self-Review Checklist

- **DB migration:** drops `obj`, adds 8 structured columns with CHECK constraints on `tier` and `status` ✓
- **Entity:** all 8 new fields present ✓
- **Repository interface:** `create` and `update` signatures match entity and use cases ✓
- **Pydantic schemas:** `SchemaField`, `ModelsSection`, `ServiceLevels` nested correctly; `DataContractUpdateModel` all-optional for partial updates ✓
- **Use cases:** pass all named params through; validate non-empty `title` ✓
- **Router:** `/yaml` route declared before `/{contract_id}` to avoid UUID parsing of the literal string `yaml` ✓
- **Router PUT:** fetches existing contract before update to apply partial patch ✓
- **Frontend types:** `DataContract` uses `tier: 1 | 2 | 3 | 4`, `status` union includes `in_review` ✓
- **Hooks:** `useDataContractYaml` uses `enabled` flag so it only fetches when the YAML modal opens ✓
- **TierWizard:** feeds `tier` field via `Controller`; has override dropdown and restart button ✓
- **ContractFields:** immutable-update pattern on `onChange`; remove by index ✓
- **DataContractForm:** `showWizard` prop controls whether TierWizard and tier select are shown; edit modal gets tier select, creation page gets wizard ✓
- **Detail page:** approval banner only renders when `status === 'in_review'`; Approve sets `active`, Request Changes sets `draft` ✓
- **Route order in App.tsx:** `/data-contracts/new` before `/data-contracts/:id` so React Router matches the literal first ✓
- **`in_review` status:** present in DB CHECK, Pydantic Literal, TypeScript union, form select, badge colors ✓
