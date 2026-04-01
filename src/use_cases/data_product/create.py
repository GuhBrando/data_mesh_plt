import uuid

from src.domain.entities.data_product import DataProduct
from src.domain.interfaces.data_product_repository import IDataProductRepository


class CreateDataProductUseCase:
    def __init__(self, repository: IDataProductRepository):
        self.repository = repository

    async def execute(
        self, name: str, description: str, data_contracts_id: uuid.UUID
    ) -> DataProduct:
        return await self.repository.create(
            name=name, description=description, data_contracts_id=data_contracts_id
        )
