from typing import Any

from src.domain.entities.data_contract import DataContract
from src.domain.interfaces.data_contract_repository import IDataContractRepository


class CreateDataContractUseCase:
    def __init__(self, repository: IDataContractRepository):
        self.repository = repository

    async def execute(self, obj: dict[str, Any]) -> DataContract:
        if not obj:
            raise ValueError("Data contract obj cannot be empty")
        return await self.repository.create(obj=obj)
