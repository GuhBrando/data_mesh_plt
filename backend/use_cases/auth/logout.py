import uuid

from fastapi import HTTPException

from backend.domain.interfaces.refresh_token_repository import IRefreshTokenRepository
from backend.infra.config import JWT_SECRET_KEY
from backend.interface.security import decode_token


class LogoutUseCase:
    def __init__(
        self, token_repo: IRefreshTokenRepository, secret_key: str = JWT_SECRET_KEY
    ):
        self.token_repo = token_repo
        self.secret_key = secret_key

    async def execute(self, refresh_token: str) -> None:
        payload = decode_token(refresh_token, secret_key=self.secret_key)
        jti = payload.get("jti")
        if not jti:
            raise HTTPException(status_code=401, detail="Invalid refresh token")
        await self.token_repo.revoke(uuid.UUID(jti))
