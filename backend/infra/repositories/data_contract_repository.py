from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    import uuid

import asyncpg

from backend.domain.entities.data_contract import DataContract
from backend.domain.interfaces.data_contract_repository import IDataContractRepository

# domain name comes from the JOIN — never stored as a denormalized text column
_SELECT = """
    SELECT dc.id, dc.title, dc.version, dc.owner,
           d.name AS domain, dc.tier, dc.status,
           dc.models, dc.servicelevels, dc.domain_id,
           dc.created_at, dc.updated_at
    FROM catalog.data_contracts dc
    JOIN catalog.domains d ON d.id = dc.domain_id
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
        domain_id: uuid.UUID,
        tier: int,
        status: str,
        models: dict[str, Any],
        servicelevels: dict[str, Any],
    ) -> DataContract:
        async with self.db.transaction():
            row = await self.db.fetchrow(
                """
                INSERT INTO catalog.data_contracts
                    (title, version, owner, domain_id, tier, status,
                     models, servicelevels)
                VALUES ($1, $2, $3, $4, $5, $6, $7::jsonb, $8::jsonb)
                RETURNING id;
                """,
                title,
                version,
                owner,
                domain_id,
                tier,
                status,
                json.dumps(models),
                json.dumps(servicelevels),
            )
            return await self.get_by_id(row["id"])

    async def get_by_id(self, contract_id: uuid.UUID) -> DataContract | None:
        row = await self.db.fetchrow(
            f"{_SELECT} WHERE dc.id = $1;",
            contract_id,
        )
        return _row_to_entity(row) if row else None

    async def list(self) -> list[DataContract]:
        rows = await self.db.fetch(f"{_SELECT} ORDER BY dc.created_at DESC;")
        return [_row_to_entity(r) for r in rows]

    async def update(
        self,
        contract_id: uuid.UUID,
        title: str,
        version: str,
        owner: str,
        domain_id: uuid.UUID,
        tier: int,
        status: str,
        models: dict[str, Any],
        servicelevels: dict[str, Any],
    ) -> DataContract | None:
        async with self.db.transaction():
            row = await self.db.fetchrow(
                """
                UPDATE catalog.data_contracts
                SET title = $1, version = $2, owner = $3, domain_id = $4,
                    tier = $5, status = $6,
                    models = $7::jsonb, servicelevels = $8::jsonb,
                    updated_at = now()
                WHERE id = $9
                RETURNING id;
                """,
                title,
                version,
                owner,
                domain_id,
                tier,
                status,
                json.dumps(models),
                json.dumps(servicelevels),
                contract_id,
            )
            if row is None:
                return None
            return await self.get_by_id(row["id"])

    async def delete(self, contract_id: uuid.UUID) -> bool:
        try:
            async with self.db.transaction():
                result = await self.db.execute(
                    "DELETE FROM catalog.data_contracts WHERE id = $1;",
                    contract_id,
                )
                return result == "DELETE 1"
        except asyncpg.ForeignKeyViolationError:
            raise ValueError(
                "Cannot delete this contract because it is still"
                " referenced by one or more data products."
                " Remove those references first."
            )

    async def list_by_domain_id(self, domain_id: uuid.UUID) -> list[DataContract]:
        rows = await self.db.fetch(
            f"{_SELECT} WHERE dc.domain_id = $1 ORDER BY dc.created_at DESC;",
            domain_id,
        )
        return [_row_to_entity(r) for r in rows]

    async def upsert(
        self,
        contract_id: uuid.UUID,
        title: str,
        version: str,
        owner: str,
        domain_id: uuid.UUID,
        tier: int,
        status: str,
        models: dict[str, Any],
        servicelevels: dict[str, Any],
    ) -> bool:
        existing = await self.get_by_id(contract_id)
        if existing is None:
            async with self.db.transaction():
                await self.db.execute(
                    """
                    INSERT INTO catalog.data_contracts
                        (id, title, version, owner, domain_id, tier, status,
                         models, servicelevels)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8::jsonb, $9::jsonb);
                    """,
                    contract_id,
                    title,
                    version,
                    owner,
                    domain_id,
                    tier,
                    status,
                    json.dumps(models),
                    json.dumps(servicelevels),
                )
            return True
        await self.update(
            contract_id=contract_id,
            title=title,
            version=version,
            owner=owner,
            domain_id=domain_id,
            tier=tier,
            status=status,
            models=models,
            servicelevels=servicelevels,
        )
        return False
