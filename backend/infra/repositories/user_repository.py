import uuid

import asyncpg

from backend.domain.entities.user import User
from backend.domain.interfaces.user_repository import IUserRepository
from backend.domain.value_objects.email import Email


class PostgresUserRepository(IUserRepository):
    def __init__(self, db):
        self.db = db

    async def create(self, name: str, email: str, password_hash: str) -> User:
        try:
            async with self.db.transaction():
                row = await self.db.fetchrow(
                    """
                    INSERT INTO iam.users (name, email, password_hash)
                    VALUES ($1, $2, $3)
                    RETURNING id, name, email, password_hash;
                    """,
                    name,
                    email,
                    password_hash,
                )
                return User(
                    id=row["id"],
                    name=row["name"],
                    email=Email(row["email"]),
                    password_hash=row["password_hash"],
                )
        except asyncpg.UniqueViolationError:
            raise ValueError("Email already in use")

    async def get_by_id(self, user_id: uuid.UUID) -> User | None:
        row = await self.db.fetchrow(
            "SELECT id, name, email, password_hash FROM iam.users WHERE id = $1;",
            user_id,
        )
        if row:
            return User(
                id=row["id"],
                name=row["name"],
                email=Email(row["email"]),
                password_hash=row["password_hash"],
            )
        return None

    async def get_by_email(self, email: str) -> User | None:
        row = await self.db.fetchrow(
            "SELECT id, name, email, password_hash FROM iam.users WHERE email = $1;",
            email,
        )
        if row:
            return User(
                id=row["id"],
                name=row["name"],
                email=Email(row["email"]),
                password_hash=row["password_hash"],
            )
        return None

    async def list(self) -> list[User]:
        rows = await self.db.fetch(
            "SELECT id, name, email, password_hash FROM iam.users;"
        )
        return [
            User(
                id=r["id"],
                name=r["name"],
                email=Email(r["email"]),
                password_hash=r["password_hash"],
            )
            for r in rows
        ]

    async def update(
        self, user_id: uuid.UUID, name: str | None, email: str | None
    ) -> User | None:
        updates: dict = {}
        if name is not None:
            updates["name"] = name
        if email is not None:
            updates["email"] = email

        if not updates:
            return await self.get_by_id(user_id)

        set_clauses = ", ".join(f"{col} = ${i + 1}" for i, col in enumerate(updates))
        values = list(updates.values()) + [user_id]

        async with self.db.transaction():
            row = await self.db.fetchrow(
                f"""
                UPDATE iam.users
                SET {set_clauses}
                WHERE id = ${len(values)}
                RETURNING id, name, email, password_hash;
                """,
                *values,
            )
            if row:
                return User(
                    id=row["id"],
                    name=row["name"],
                    email=Email(row["email"]),
                    password_hash=row["password_hash"],
                )
            return None

    async def delete(self, user_id: uuid.UUID) -> bool:
        async with self.db.transaction():
            result = await self.db.execute(
                "DELETE FROM iam.users WHERE id = $1;",
                user_id,
            )
            return result == "DELETE 1"
