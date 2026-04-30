import uuid
from abc import ABC, abstractmethod

from backend.domain.entities.user import User
from backend.domain.value_objects.user_role import UserRole


class IUserRepository(ABC):
    @abstractmethod
    async def create(self, name: str, email: str, password_hash: str) -> User: ...

    @abstractmethod
    async def get_by_id(self, user_id: uuid.UUID) -> User | None: ...

    @abstractmethod
    async def get_by_email(self, email: str) -> User | None: ...

    @abstractmethod
    async def list(self) -> list[User]: ...

    @abstractmethod
    async def update(
        self, user_id: uuid.UUID, name: str | None, email: str | None
    ) -> User | None: ...

    @abstractmethod
    async def delete(self, user_id: uuid.UUID) -> bool: ...

    @abstractmethod
    async def assign_role(self, user_id: uuid.UUID, role: UserRole) -> User | None: ...

    @abstractmethod
    async def change_password(self, user_id: uuid.UUID, new_hash: str) -> None: ...
