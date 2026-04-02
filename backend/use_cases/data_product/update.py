import uuid

from backend.domain.entities.data_product import DataProduct
from backend.domain.interfaces.data_product_repository import IDataProductRepository


class UpdateDataProductUseCase:
    def __init__(self, repository: IDataProductRepository):
        self.repository = repository

    async def execute(
        self,
        product_id: uuid.UUID,
        name: str | None,
        description: str | None,
        data_contracts_id: uuid.UUID | None,
    ) -> DataProduct | None:
        return await self.repository.update(
            product_id=product_id,
            name=name,
            description=description,
            data_contracts_id=data_contracts_id,
        )
