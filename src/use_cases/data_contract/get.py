import uuid

from src.domain.entities.data_contract import DataContract
from src.domain.interfaces.data_contract_repository import IDataContractRepository


class GetDataContractUseCase:
    def __init__(self, repository: IDataContractRepository):
        self.repository = repository

    async def execute(self, contract_id: uuid.UUID) -> DataContract | None:
        return await self.repository.get_by_id(contract_id)
