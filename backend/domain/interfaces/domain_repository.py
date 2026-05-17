import uuid
from abc import ABC, abstractmethod

from backend.domain.entities.domain import Domain, DomainMember


class IDomainRepository(ABC):
    @abstractmethod
    async def create(
        self, name: str, description: str, owner_id: uuid.UUID | None
    ) -> Domain: ...

    @abstractmethod
    async def get_by_id(self, domain_id: uuid.UUID) -> Domain | None: ...

    @abstractmethod
    async def find_by_name(self, name: str) -> Domain | None: ...

    @abstractmethod
    async def list(self) -> list[Domain]: ...

    @abstractmethod
    async def update(
        self,
        domain_id: uuid.UUID,
        name: str | None,
        description: str | None,
        owner_id: uuid.UUID | None,
    ) -> Domain | None: ...

    @abstractmethod
    async def delete(self, domain_id: uuid.UUID) -> bool: ...

    @abstractmethod
    async def add_member(
        self, domain_id: uuid.UUID, user_id: uuid.UUID, role: str
    ) -> DomainMember: ...

    @abstractmethod
    async def update_member_role(
        self, domain_id: uuid.UUID, user_id: uuid.UUID, role: str
    ) -> DomainMember | None: ...

    @abstractmethod
    async def remove_member(self, domain_id: uuid.UUID, user_id: uuid.UUID) -> None: ...

    @abstractmethod
    async def is_member(self, domain_id: uuid.UUID, user_id: uuid.UUID) -> bool: ...
