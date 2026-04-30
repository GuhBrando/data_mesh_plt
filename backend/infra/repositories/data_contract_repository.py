import json
import uuid
from typing import Any

from backend.domain.entities.data_contract import DataContract
from backend.domain.interfaces.data_contract_repository import IDataContractRepository

_SELECT = """
    SELECT id, title, version, owner, domain, tier, status,
           models, servicelevels, domain_id, created_at, updated_at
    FROM catalog.data_contracts
"""

_RETURNING = """
    RETURNING id, title, version, owner, domain, tier, status,
              models, servicelevels, domain_id, created_at, updated_at
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
        domain_id=row["domain_id"],
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
        domain_id: uuid.UUID | None = None,
    ) -> DataContract:
        async with self.db.transaction():
            row = await self.db.fetchrow(
                f"""
                INSERT INTO catalog.data_contracts
                    (title, version, owner, domain, tier, status,
                     models, servicelevels, domain_id)
                VALUES ($1, $2, $3, $4, $5, $6, $7::jsonb, $8::jsonb, $9)
                {_RETURNING};
                """,
                title,
                version,
                owner,
                domain,
                tier,
                status,
                json.dumps(models),
                json.dumps(servicelevels),
                domain_id,
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
                f"""
                UPDATE catalog.data_contracts
                SET title = $1, version = $2, owner = $3, domain = $4,
                    tier = $5, status = $6,
                    models = $7::jsonb, servicelevels = $8::jsonb,
                    updated_at = now()
                WHERE id = $9
                {_RETURNING};
                """,
                title,
                version,
                owner,
                domain,
                tier,
                status,
                json.dumps(models),
                json.dumps(servicelevels),
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
