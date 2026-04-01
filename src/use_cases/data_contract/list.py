from src.domain.entities.data_contract import DataContract
from src.domain.interfaces.data_contract_repository import IDataContractRepository


class ListDataContractsUseCase:
    def __init__(self, repository: IDataContractRepository):
        self.repository = repository

    async def execute(self) -> list[DataContract]:
        return await self.repository.list()
