import uuid

from src.domain.interfaces.data_contract_repository import IDataContractRepository


class DeleteDataContractUseCase:
    def __init__(self, repository: IDataContractRepository):
        self.repository = repository

    async def execute(self, contract_id: uuid.UUID) -> bool:
        return await self.repository.delete(contract_id)
