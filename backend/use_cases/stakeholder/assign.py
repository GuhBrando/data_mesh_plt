import uuid

from backend.domain.entities.contract_stakeholder import ContractStakeholder
from backend.domain.interfaces.stakeholder_repository import IStakeholderRepository


class AssignStakeholderUseCase:
    def __init__(self, repository: IStakeholderRepository):
        self.repository = repository

    async def execute(
        self, contract_id: uuid.UUID, user_id: uuid.UUID, assigned_by: uuid.UUID
    ) -> ContractStakeholder:
        return await self.repository.assign(contract_id, user_id, assigned_by)
