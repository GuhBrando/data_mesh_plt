import uuid

from backend.domain.interfaces.domain_repository import IDomainRepository


class DeleteDomainUseCase:
    def __init__(self, repository: IDomainRepository):
        self.repository = repository

    async def execute(self, domain_id: uuid.UUID) -> bool:
        return await self.repository.delete(domain_id)
