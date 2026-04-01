import uuid

from src.domain.interfaces.data_product_repository import IDataProductRepository


class DeleteDataProductUseCase:
    def __init__(self, repository: IDataProductRepository):
        self.repository = repository

    async def execute(self, product_id: uuid.UUID) -> bool:
        return await self.repository.delete(product_id)
