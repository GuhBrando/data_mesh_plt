import hashlib
import uuid

from fastapi import HTTPException

from backend.domain.interfaces.refresh_token_repository import IRefreshTokenRepository
from backend.infra.config import JWT_SECRET_KEY
from backend.interface.security import create_access_token, decode_token


class RefreshUseCase:
    def __init__(
        self, token_repo: IRefreshTokenRepository, secret_key: str = JWT_SECRET_KEY
    ):
        self.token_repo = token_repo
        self.secret_key = secret_key

    async def execute(self, refresh_token: str) -> dict:
        payload = decode_token(refresh_token, secret_key=self.secret_key)
        jti = payload.get("jti")
        user_id = payload.get("sub")
        if not jti or not user_id:
            raise HTTPException(status_code=401, detail="Invalid refresh token")

        stored = await self.token_repo.get_by_id(uuid.UUID(jti))
        token_hash = hashlib.sha256(refresh_token.encode()).hexdigest()
        if not stored or stored.revoked or stored.token_hash != token_hash:
            raise HTTPException(status_code=401, detail="Invalid refresh token")

        access_token = create_access_token(user_id=user_id, secret_key=self.secret_key)
        return {"access_token": access_token, "token_type": "bearer"}
