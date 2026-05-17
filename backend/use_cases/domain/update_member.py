import uuid

from fastapi import HTTPException

from backend.domain.entities.domain import DomainMember
from backend.domain.interfaces.domain_repository import IDomainRepository


class UpdateDomainMemberUseCase:
    def __init__(self, repository: IDomainRepository):
        self.repository = repository

    async def execute(
        self, domain_id: uuid.UUID, user_id: uuid.UUID, role: str
    ) -> DomainMember:
        if role not in ("maintainer", "member"):
            raise HTTPException(
                status_code=400, detail="Role must be 'maintainer' or 'member'"
            )
        member = await self.repository.update_member_role(
            domain_id=domain_id, user_id=user_id, role=role
        )
        if not member:
            raise HTTPException(status_code=404, detail="Member not found")
        return member
