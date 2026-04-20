import hashlib
import uuid
from datetime import UTC, datetime, timedelta

import bcrypt
from fastapi import HTTPException

from backend.domain.interfaces.refresh_token_repository import IRefreshTokenRepository
from backend.domain.interfaces.user_repository import IUserRepository
from backend.infra.config import JWT_REFRESH_TOKEN_EXPIRE_DAYS
from backend.interface.security import create_access_token, create_refresh_token


class LoginUseCase:
    def __init__(self, user_repo: IUserRepository, token_repo: IRefreshTokenRepository):
        self.user_repo = user_repo
        self.token_repo = token_repo

    async def execute(self, email: str, password: str) -> dict:
        user = await self.user_repo.get_by_email(email)
        if not user or not bcrypt.checkpw(
            password.encode(), user.password_hash.encode()
        ):
            raise HTTPException(status_code=401, detail="Invalid credentials")

        jti = str(uuid.uuid4())
        access_token = create_access_token(user_id=str(user.id))
        refresh_token = create_refresh_token(jti=jti, user_id=str(user.id))

        token_hash = hashlib.sha256(refresh_token.encode()).hexdigest()
        expires_at = datetime.now(UTC) + timedelta(days=JWT_REFRESH_TOKEN_EXPIRE_DAYS)
        await self.token_repo.create(
            id=uuid.UUID(jti),
            user_id=user.id,
            token_hash=token_hash,
            expires_at=expires_at,
        )
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
        }
