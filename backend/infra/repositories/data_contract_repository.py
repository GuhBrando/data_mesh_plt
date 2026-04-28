import json
import uuid
from typing import Any

from backend.domain.entities.data_contract import DataContract
from backend.domain.interfaces.data_contract_repository import IDataContractRepository

_COLUMNS = (
    "id, title, version, owner, domain, tier, status, models, servicelevels,"
    " domain_id, created_at, updated_at"
)

_DEFAULT_SERVICELEVELS = {
    "latency": "",
    "freshness": "",
    "retention": "",
    "availability": "",
}


def _parse_json(value) -> dict:
    if isinstance(value, str):
        return json.loads(value)
    return dict(value)


def _row_to_contract(row) -> DataContract:
    obj = {
        "title": row["title"],
        "version": row["version"],
        "owner": row["owner"],
        "domain": row["domain"],
        "tier": row["tier"],
        "status": row["status"],
        "models": _parse_json(row["models"]),
        "servicelevels": _parse_json(row["servicelevels"]),
    }
    return DataContract(
        id=row["id"],
        obj=obj,
        created_at=row["created_at"],
        updated_at=row["updated_at"],
        domain_id=row["domain_id"],
    )


def _obj_params(obj: dict[str, Any]) -> tuple:
    return (
        obj.get("title", ""),
        obj.get("version", "1.0.0"),
        obj.get("owner", ""),
        obj.get("domain", ""),
        obj.get("tier", 4),
        obj.get("status", "draft"),
        json.dumps(obj.get("models", {"fields": []})),
        json.dumps(obj.get("servicelevels", _DEFAULT_SERVICELEVELS)),
    )


class PostgresDataContractRepository(IDataContractRepository):
    def __init__(self, db):
        self.db = db

    async def create(
        self, obj: dict[str, Any], domain_id: uuid.UUID | None = None
    ) -> DataContract:
        title, version, owner, domain, tier, status, models, servicelevels = (
            _obj_params(obj)
        )
        async with self.db.transaction():
            row = await self.db.fetchrow(
                f"""
                INSERT INTO catalog.data_contracts
                    (title, version, owner, domain, tier, status,
                     models, servicelevels, domain_id)
                VALUES ($1, $2, $3, $4, $5, $6, $7::jsonb, $8::jsonb, $9)
                RETURNING {_COLUMNS};
                """,
                title,
                version,
                owner,
                domain,
                tier,
                status,
                models,
                servicelevels,
                domain_id,
            )
            return _row_to_contract(row)

    async def get_by_id(self, contract_id: uuid.UUID) -> DataContract | None:
        row = await self.db.fetchrow(
            f"SELECT {_COLUMNS} FROM catalog.data_contracts WHERE id = $1;",
            contract_id,
        )
        return _row_to_contract(row) if row else None

    async def list(self) -> list[DataContract]:
        rows = await self.db.fetch(f"SELECT {_COLUMNS} FROM catalog.data_contracts;")
        return [_row_to_contract(r) for r in rows]

    async def update(
        self, contract_id: uuid.UUID, obj: dict[str, Any]
    ) -> DataContract | None:
        title, version, owner, domain, tier, status, models, servicelevels = (
            _obj_params(obj)
        )
        async with self.db.transaction():
            row = await self.db.fetchrow(
                f"""
                UPDATE catalog.data_contracts
                SET title = $1, version = $2, owner = $3, domain = $4,
                    tier = $5, status = $6,
                    models = $7::jsonb, servicelevels = $8::jsonb,
                    updated_at = now()
                WHERE id = $9
                RETURNING {_COLUMNS};
                """,
                title,
                version,
                owner,
                domain,
                tier,
                status,
                models,
                servicelevels,
                contract_id,
            )
            return _row_to_contract(row) if row else None

    async def delete(self, contract_id: uuid.UUID) -> bool:
        async with self.db.transaction():
            result = await self.db.execute(
                "DELETE FROM catalog.data_contracts WHERE id = $1;",
                contract_id,
            )
            return result == "DELETE 1"
