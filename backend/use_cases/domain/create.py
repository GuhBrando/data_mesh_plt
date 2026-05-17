import uuid

from fastapi import HTTPException

from backend.domain.entities.domain import Domain
from backend.domain.interfaces.domain_repository import IDomainRepository


class CreateDomainUseCase:
    def __init__(self, repository: IDomainRepository):
        self.repository = repository

    async def execute(
        self, name: str, description: str = "", owner_id: uuid.UUID | None = None
    ) -> Domain:
        if not name or not name.strip():
            raise HTTPException(status_code=400, detail="Domain name cannot be empty")
        return await self.repository.create(name.strip(), description, owner_id)
