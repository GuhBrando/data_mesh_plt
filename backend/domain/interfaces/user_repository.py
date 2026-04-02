import uuid
from abc import ABC, abstractmethod

from backend.domain.entities.user import User


class IUserRepository(ABC):
    @abstractmethod
    async def create(self, name: str, email: str) -> User: ...

    @abstractmethod
    async def get_by_id(self, user_id: uuid.UUID) -> User | None: ...

    @abstractmethod
    async def list(self) -> list[User]: ...

    @abstractmethod
    async def update(
        self, user_id: uuid.UUID, name: str | None, email: str | None
    ) -> User | None: ...

    @abstractmethod
    async def delete(self, user_id: uuid.UUID) -> bool: ...
