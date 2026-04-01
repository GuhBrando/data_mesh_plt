import json
import uuid
from typing import Any

from src.domain.entities.data_contract import DataContract
from src.domain.interfaces.data_contract_repository import IDataContractRepository


class PostgresDataContractRepository(IDataContractRepository):
    def __init__(self, db):
        self.db = db

    async def create(self, obj: dict[str, Any]) -> DataContract:
        async with self.db.transaction():
            row = await self.db.fetchrow(
                """
                INSERT INTO catalog.data_contracts (obj)
                VALUES ($1::jsonb)
                RETURNING id, obj, created_at, updated_at;
                """,
                json.dumps(obj),
            )
            return DataContract(
                id=row["id"],
                obj=row["obj"],
                created_at=row["created_at"],
                updated_at=row["updated_at"],
            )

    async def get_by_id(self, contract_id: uuid.UUID) -> DataContract | None:
        row = await self.db.fetchrow(
            "SELECT id, obj, created_at, updated_at"
            " FROM catalog.data_contracts WHERE id = $1;",
            contract_id,
        )
        if row:
            return DataContract(
                id=row["id"],
                obj=row["obj"],
                created_at=row["created_at"],
                updated_at=row["updated_at"],
            )
        return None

    async def list(self) -> list[DataContract]:
        rows = await self.db.fetch(
            "SELECT id, obj, created_at, updated_at FROM catalog.data_contracts;"
        )
        return [
            DataContract(
                id=r["id"],
                obj=r["obj"],
                created_at=r["created_at"],
                updated_at=r["updated_at"],
            )
            for r in rows
        ]

    async def update(
        self, contract_id: uuid.UUID, obj: dict[str, Any]
    ) -> DataContract | None:
        async with self.db.transaction():
            row = await self.db.fetchrow(
                """
                UPDATE catalog.data_contracts
                SET obj = $1::jsonb, updated_at = now()
                WHERE id = $2
                RETURNING id, obj, created_at, updated_at;
                """,
                json.dumps(obj),
                contract_id,
            )
            if row:
                return DataContract(
                    id=row["id"],
                    obj=row["obj"],
                    created_at=row["created_at"],
                    updated_at=row["updated_at"],
                )
            return None

    async def delete(self, contract_id: uuid.UUID) -> bool:
        async with self.db.transaction():
            result = await self.db.execute(
                "DELETE FROM catalog.data_contracts WHERE id = $1;",
                contract_id,
            )
            return result == "DELETE 1"
