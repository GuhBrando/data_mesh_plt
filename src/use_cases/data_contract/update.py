import uuid
from typing import Any

from src.domain.entities.data_contract import DataContract
from src.domain.interfaces.data_contract_repository import IDataContractRepository


class UpdateDataContractUseCase:
    def __init__(self, repository: IDataContractRepository):
        self.repository = repository

    async def execute(
        self, contract_id: uuid.UUID, obj: dict[str, Any]
    ) -> DataContract | None:
        if not obj:
            raise ValueError("Data contract obj cannot be empty")
        return await self.repository.update(contract_id=contract_id, obj=obj)
