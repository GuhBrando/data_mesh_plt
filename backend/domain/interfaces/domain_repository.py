import uuid
from abc import ABC, abstractmethod

from backend.domain.entities.domain import Domain


class IDomainRepository(ABC):
    @abstractmethod
    async def create(self, name: str) -> Domain: ...

    @abstractmethod
    async def get_by_id(self, domain_id: uuid.UUID) -> Domain | None: ...

    @abstractmethod
    async def add_member(self, domain_id: uuid.UUID, user_id: uuid.UUID) -> None: ...

    @abstractmethod
    async def remove_member(self, domain_id: uuid.UUID, user_id: uuid.UUID) -> None: ...

    @abstractmethod
    async def is_member(self, domain_id: uuid.UUID, user_id: uuid.UUID) -> bool: ...
