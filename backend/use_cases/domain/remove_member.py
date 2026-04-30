import uuid

from backend.domain.interfaces.domain_repository import IDomainRepository


class RemoveDomainMemberUseCase:
    def __init__(self, repository: IDomainRepository):
        self.repository = repository

    async def execute(self, domain_id: uuid.UUID, user_id: uuid.UUID) -> None:
        await self.repository.remove_member(domain_id=domain_id, user_id=user_id)
