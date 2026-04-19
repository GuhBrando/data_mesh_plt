from backend.domain.entities.data_product import DataProduct
from backend.domain.interfaces.data_product_repository import IDataProductRepository


class ListDataProductsUseCase:
    def __init__(self, repository: IDataProductRepository):
        self.repository = repository

    async def execute(self) -> list[DataProduct]:
        return await self.repository.list()
