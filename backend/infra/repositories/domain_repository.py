import uuid

from backend.domain.entities.domain import Domain
from backend.domain.interfaces.domain_repository import IDomainRepository


class PostgresDomainRepository(IDomainRepository):
    def __init__(self, db):
        self.db = db

    async def create(self, name: str) -> Domain:
        async with self.db.transaction():
            row = await self.db.fetchrow(
                """
                INSERT INTO iam.principals (name, type)
                VALUES ($1, 'GROUP')
                RETURNING id, name;
                """,
                name,
            )
            return Domain(id=row["id"], name=row["name"])

    async def get_by_id(self, domain_id: uuid.UUID) -> Domain | None:
        row = await self.db.fetchrow(
            "SELECT id, name FROM iam.principals WHERE id = $1 AND type = 'GROUP';",
            domain_id,
        )
        return Domain(id=row["id"], name=row["name"]) if row else None

    async def add_member(self, domain_id: uuid.UUID, user_id: uuid.UUID) -> None:
        await self.db.execute(
            """
            INSERT INTO iam.principal_memberships (users_id, principals_id)
            VALUES ($1, $2)
            ON CONFLICT DO NOTHING;
            """,
            user_id,
            domain_id,
        )

    async def remove_member(self, domain_id: uuid.UUID, user_id: uuid.UUID) -> None:
        await self.db.execute(
            """
            DELETE FROM iam.principal_memberships
            WHERE users_id = $1 AND principals_id = $2;
            """,
            user_id,
            domain_id,
        )

    async def is_member(self, domain_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        row = await self.db.fetchrow(
            """
            SELECT 1 FROM iam.principal_memberships
            WHERE users_id = $1 AND principals_id = $2;
            """,
            user_id,
            domain_id,
        )
        return row is not None
