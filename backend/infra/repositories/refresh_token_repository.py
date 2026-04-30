import uuid
from datetime import datetime

from backend.domain.entities.refresh_token import RefreshToken
from backend.domain.interfaces.refresh_token_repository import IRefreshTokenRepository


class PostgresRefreshTokenRepository(IRefreshTokenRepository):
    def __init__(self, db):
        self.db = db

    async def create(
        self,
        id: uuid.UUID,
        user_id: uuid.UUID,
        token_hash: str,
        expires_at: datetime,
    ) -> RefreshToken:
        async with self.db.transaction():
            row = await self.db.fetchrow(
                """
                INSERT INTO iam.refresh_tokens (id, user_id, token_hash, expires_at)
                VALUES ($1, $2, $3, $4)
                RETURNING id, user_id, token_hash, expires_at, revoked;
                """,
                id,
                user_id,
                token_hash,
                expires_at,
            )
            return RefreshToken(
                id=row["id"],
                user_id=row["user_id"],
                token_hash=row["token_hash"],
                expires_at=row["expires_at"],
                revoked=row["revoked"],
            )

    async def get_by_id(self, token_id: uuid.UUID) -> RefreshToken | None:
        row = await self.db.fetchrow(
            """
            SELECT id, user_id, token_hash, expires_at, revoked
            FROM iam.refresh_tokens
            WHERE id = $1;
            """,
            token_id,
        )
        if row:
            return RefreshToken(
                id=row["id"],
                user_id=row["user_id"],
                token_hash=row["token_hash"],
                expires_at=row["expires_at"],
                revoked=row["revoked"],
            )
        return None

    async def revoke(self, token_id: uuid.UUID) -> None:
        await self.db.execute(
            "UPDATE iam.refresh_tokens SET revoked = true WHERE id = $1;",
            token_id,
        )

    async def revoke_all_for_user(self, user_id: uuid.UUID) -> None:
        await self.db.execute(
            "UPDATE iam.refresh_tokens SET revoked = true WHERE user_id = $1;",
            user_id,
        )
