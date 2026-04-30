import uuid

from fastapi import HTTPException

from backend.domain.interfaces.domain_repository import IDomainRepository


class AddDomainMemberUseCase:
    def __init__(self, repository: IDomainRepository):
        self.repository = repository

    async def execute(self, domain_id: uuid.UUID, user_id: uuid.UUID) -> None:
        domain = await self.repository.get_by_id(domain_id)
        if not domain:
            raise HTTPException(status_code=404, detail="Domain not found")
        await self.repository.add_member(domain_id=domain_id, user_id=user_id)
