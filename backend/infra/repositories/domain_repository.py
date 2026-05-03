import json
import uuid

from backend.domain.entities.domain import Domain, DomainMember
from backend.domain.interfaces.domain_repository import IDomainRepository

_RICH_SELECT = """
    SELECT
        p.id,
        p.name,
        p.description,
        p.owner_id,
        COALESCE(ou.name, '')          AS owner_username,
        p.created_at,
        p.updated_at,
        COUNT(DISTINCT dc.id)::int     AS contract_count,
        COALESCE(
            json_agg(
                json_build_object(
                    'user_id',  pm.users_id,
                    'username', mu.name,
                    'role',     pm.role
                )
                ORDER BY mu.name
            ) FILTER (WHERE pm.users_id IS NOT NULL),
            '[]'::json
        ) AS members
    FROM iam.principals p
    LEFT JOIN iam.users ou ON ou.id = p.owner_id
    LEFT JOIN iam.principal_memberships pm ON pm.principals_id = p.id
    LEFT JOIN iam.users mu ON mu.id = pm.users_id
    LEFT JOIN catalog.data_contracts dc ON dc.domain_id = p.id
    WHERE p.type = 'GROUP'
"""


def _row_to_domain(row) -> Domain:
    raw = row["members"]
    members_data = json.loads(raw) if isinstance(raw, str) else raw or []

    members = [
        DomainMember(
            user_id=uuid.UUID(str(m["user_id"])),
            username=m["username"],
            role=m["role"],
        )
        for m in members_data
    ]
    return Domain(
        id=row["id"],
        name=row["name"],
        description=row["description"],
        owner_id=row["owner_id"],
        owner_username=row["owner_username"] or "",
        members=members,
        contract_count=row["contract_count"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


class PostgresDomainRepository(IDomainRepository):
    def __init__(self, db):
        self.db = db

    async def create(
        self, name: str, description: str, owner_id: uuid.UUID | None
    ) -> Domain:
        async with self.db.transaction():
            row = await self.db.fetchrow(
                """
                INSERT INTO iam.principals (name, type, description, owner_id)
                VALUES ($1, 'GROUP', $2, $3)
                RETURNING id;
                """,
                name,
                description,
                owner_id,
            )
            return await self._get_rich(row["id"])

    async def get_by_id(self, domain_id: uuid.UUID) -> Domain | None:
        return await self._get_rich(domain_id)

    async def list(self) -> list[Domain]:
        query = (
            _RICH_SELECT
            + " GROUP BY p.id, p.name, p.description, p.owner_id,"
            + " ou.name, p.created_at, p.updated_at ORDER BY p.name;"
        )
        rows = await self.db.fetch(query)
        return [_row_to_domain(r) for r in rows]

    async def update(
        self,
        domain_id: uuid.UUID,
        name: str | None,
        description: str | None,
        owner_id: uuid.UUID | None,
    ) -> Domain | None:
        existing = await self.db.fetchrow(
            "SELECT id FROM iam.principals WHERE id = $1 AND type = 'GROUP';",
            domain_id,
        )
        if not existing:
            return None

        if name is not None:
            await self.db.execute(
                "UPDATE iam.principals"
                " SET name = $1, updated_at = now() WHERE id = $2;",
                name,
                domain_id,
            )
        if description is not None:
            await self.db.execute(
                "UPDATE iam.principals"
                " SET description = $1, updated_at = now() WHERE id = $2;",
                description,
                domain_id,
            )
        if owner_id is not None:
            await self.db.execute(
                "UPDATE iam.principals"
                " SET owner_id = $1, updated_at = now() WHERE id = $2;",
                owner_id,
                domain_id,
            )
        return await self._get_rich(domain_id)

    async def delete(self, domain_id: uuid.UUID) -> bool:
        result = await self.db.execute(
            "DELETE FROM iam.principals WHERE id = $1 AND type = 'GROUP';",
            domain_id,
        )
        return result != "DELETE 0"

    async def add_member(
        self, domain_id: uuid.UUID, user_id: uuid.UUID, role: str
    ) -> DomainMember:
        await self.db.execute(
            """
            INSERT INTO iam.principal_memberships (users_id, principals_id, role)
            VALUES ($1, $2, $3)
            ON CONFLICT (users_id, principals_id)
            DO UPDATE SET role = EXCLUDED.role;
            """,
            user_id,
            domain_id,
            role,
        )
        row = await self.db.fetchrow(
            "SELECT u.name FROM iam.users u WHERE u.id = $1;",
            user_id,
        )
        return DomainMember(
            user_id=user_id, username=row["name"] if row else "", role=role
        )

    async def update_member_role(
        self, domain_id: uuid.UUID, user_id: uuid.UUID, role: str
    ) -> DomainMember | None:
        result = await self.db.execute(
            """
            UPDATE iam.principal_memberships
            SET role = $1
            WHERE users_id = $2 AND principals_id = $3;
            """,
            role,
            user_id,
            domain_id,
        )
        if result == "UPDATE 0":
            return None
        row = await self.db.fetchrow(
            "SELECT u.name FROM iam.users u WHERE u.id = $1;",
            user_id,
        )
        return DomainMember(
            user_id=user_id, username=row["name"] if row else "", role=role
        )

    async def remove_member(self, domain_id: uuid.UUID, user_id: uuid.UUID) -> None:
        await self.db.execute(
            "DELETE FROM iam.principal_memberships"
            " WHERE users_id = $1 AND principals_id = $2;",
            user_id,
            domain_id,
        )

    async def is_member(self, domain_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        row = await self.db.fetchrow(
            "SELECT 1 FROM iam.principal_memberships"
            " WHERE users_id = $1 AND principals_id = $2;",
            user_id,
            domain_id,
        )
        return row is not None

    async def _get_rich(self, domain_id: uuid.UUID) -> Domain | None:
        query = (
            _RICH_SELECT
            + " AND p.id = $1"
            + " GROUP BY p.id, p.name, p.description, p.owner_id,"
            + " ou.name, p.created_at, p.updated_at;"
        )
        row = await self.db.fetchrow(query, domain_id)
        return _row_to_domain(row) if row else None
