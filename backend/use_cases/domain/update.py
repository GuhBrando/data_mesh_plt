import uuid

from backend.domain.entities.domain import Domain
from backend.domain.interfaces.domain_repository import IDomainRepository


class UpdateDomainUseCase:
    def __init__(self, repository: IDomainRepository):
        self.repository = repository

    async def execute(
        self,
        domain_id: uuid.UUID,
        name: str | None = None,
        description: str | None = None,
        owner_id: uuid.UUID | None = None,
    ) -> Domain | None:
        return await self.repository.update(
            domain_id=domain_id,
            name=name,
            description=description,
            owner_id=owner_id,
        )
