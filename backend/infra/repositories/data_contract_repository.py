import json
import uuid
from typing import Any

from backend.domain.entities.data_contract import DataContract
from backend.domain.interfaces.data_contract_repository import IDataContractRepository


def _row_to_contract(row) -> DataContract:
    return DataContract(
        id=row["id"],
        obj=row["obj"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
        domain_id=row["domain_id"],
    )


class PostgresDataContractRepository(IDataContractRepository):
    def __init__(self, db):
        self.db = db

    async def create(
        self, obj: dict[str, Any], domain_id: uuid.UUID | None = None
    ) -> DataContract:
        async with self.db.transaction():
            row = await self.db.fetchrow(
                """
                INSERT INTO catalog.data_contracts (obj, domain_id)
                VALUES ($1::jsonb, $2)
                RETURNING id, obj, domain_id, created_at, updated_at;
                """,
                json.dumps(obj),
                domain_id,
            )
            return _row_to_contract(row)

    async def get_by_id(self, contract_id: uuid.UUID) -> DataContract | None:
        row = await self.db.fetchrow(
            "SELECT id, obj, domain_id, created_at, updated_at"
            " FROM catalog.data_contracts WHERE id = $1;",
            contract_id,
        )
        return _row_to_contract(row) if row else None

    async def list(self) -> list[DataContract]:
        rows = await self.db.fetch(
            "SELECT id, obj, domain_id, created_at, updated_at"
            " FROM catalog.data_contracts;"
        )
        return [_row_to_contract(r) for r in rows]

    async def update(
        self, contract_id: uuid.UUID, obj: dict[str, Any]
    ) -> DataContract | None:
        async with self.db.transaction():
            row = await self.db.fetchrow(
                """
                UPDATE catalog.data_contracts
                SET obj = $1::jsonb, updated_at = now()
                WHERE id = $2
                RETURNING id, obj, domain_id, created_at, updated_at;
                """,
                json.dumps(obj),
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
