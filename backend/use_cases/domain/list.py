from backend.domain.entities.domain import Domain
from backend.domain.interfaces.domain_repository import IDomainRepository


class ListDomainsUseCase:
    def __init__(self, repository: IDomainRepository):
        self.repository = repository

    async def execute(self) -> list[Domain]:
        return await self.repository.list()
