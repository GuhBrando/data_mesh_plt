import uuid
from abc import ABC, abstractmethod

from src.domain.entities.data_product import DataProduct


class IDataProductRepository(ABC):
    @abstractmethod
    async def create(
        self, name: str, description: str, data_contracts_id: uuid.UUID
    ) -> DataProduct: ...

    @abstractmethod
    async def get_by_id(self, product_id: uuid.UUID) -> DataProduct | None: ...

    @abstractmethod
    async def list(self) -> list[DataProduct]: ...

    @abstractmethod
    async def update(
        self,
        product_id: uuid.UUID,
        name: str | None,
        description: str | None,
        data_contracts_id: uuid.UUID | None,
    ) -> DataProduct | None: ...

    @abstractmethod
    async def delete(self, product_id: uuid.UUID) -> bool: ...
