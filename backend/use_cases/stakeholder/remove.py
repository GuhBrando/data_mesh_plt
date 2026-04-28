import uuid

from fastapi import HTTPException

from backend.domain.interfaces.stakeholder_repository import IStakeholderRepository


class RemoveStakeholderUseCase:
    def __init__(self, repository: IStakeholderRepository):
        self.repository = repository

    async def execute(self, contract_id: uuid.UUID, user_id: uuid.UUID) -> None:
        removed = await self.repository.remove(contract_id, user_id)
        if not removed:
            raise HTTPException(status_code=404, detail="Stakeholder not found")
