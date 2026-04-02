import uuid

from backend.domain.entities.data_product import DataProduct
from backend.domain.interfaces.data_product_repository import IDataProductRepository


class PostgresDataProductRepository(IDataProductRepository):
    def __init__(self, db):
        self.db = db

    async def create(
        self, name: str, description: str, data_contracts_id: uuid.UUID
    ) -> DataProduct:
        async with self.db.transaction():
            row = await self.db.fetchrow(
                """
                INSERT INTO catalog.data_products (name, description, data_contracts_id)
                VALUES ($1, $2, $3)
                RETURNING id, name, description,
                data_contracts_id, created_at, updated_at;
                """,
                name,
                description,
                data_contracts_id,
            )
            return DataProduct(
                id=row["id"],
                name=row["name"],
                description=row["description"],
                data_contracts_id=row["data_contracts_id"],
                created_at=row["created_at"],
                updated_at=row["updated_at"],
            )

    async def get_by_id(self, product_id: uuid.UUID) -> DataProduct | None:
        row = await self.db.fetchrow(
            """
            SELECT id, name, description, data_contracts_id, created_at, updated_at
            FROM catalog.data_products WHERE id = $1;
            """,
            product_id,
        )
        if row:
            return DataProduct(
                id=row["id"],
                name=row["name"],
                description=row["description"],
                data_contracts_id=row["data_contracts_id"],
                created_at=row["created_at"],
                updated_at=row["updated_at"],
            )
        return None

    async def list(self) -> list[DataProduct]:
        rows = await self.db.fetch(
            """
            SELECT id, name, description, data_contracts_id, created_at, updated_at
            FROM catalog.data_products;
            """
        )
        return [
            DataProduct(
                id=r["id"],
                name=r["name"],
                description=r["description"],
                data_contracts_id=r["data_contracts_id"],
                created_at=r["created_at"],
                updated_at=r["updated_at"],
            )
            for r in rows
        ]

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
                RETURNING id, name, description,
                data_contracts_id, created_at, updated_at;
                """,
                *values,
            )
            if row:
                return DataProduct(
                    id=row["id"],
                    name=row["name"],
                    description=row["description"],
                    data_contracts_id=row["data_contracts_id"],
                    created_at=row["created_at"],
                    updated_at=row["updated_at"],
                )
            return None

    async def delete(self, product_id: uuid.UUID) -> bool:
        async with self.db.transaction():
            result = await self.db.execute(
                "DELETE FROM catalog.data_products WHERE id = $1;",
                product_id,
            )
            return result == "DELETE 1"
