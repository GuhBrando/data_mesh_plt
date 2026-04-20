import uuid
from abc import ABC, abstractmethod
from datetime import datetime

from backend.domain.entities.refresh_token import RefreshToken


class IRefreshTokenRepository(ABC):
    @abstractmethod
    async def create(
        self,
        id: uuid.UUID,
        user_id: uuid.UUID,
        token_hash: str,
        expires_at: datetime,
    ) -> RefreshToken: ...

    @abstractmethod
    async def get_by_id(self, token_id: uuid.UUID) -> RefreshToken | None: ...

    @abstractmethod
    async def revoke(self, token_id: uuid.UUID) -> None: ...
