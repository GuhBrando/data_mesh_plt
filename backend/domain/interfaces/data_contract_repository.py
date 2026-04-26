import uuid
from abc import ABC, abstractmethod
from typing import Any

from backend.domain.entities.data_contract import DataContract


class IDataContractRepository(ABC):
    @abstractmethod
    async def create(
        self,
        title: str,
        version: str,
        owner: str,
        domain: str,
        tier: int,
        status: str,
        models: dict[str, Any],
        servicelevels: dict[str, Any],
    ) -> DataContract: ...

    @abstractmethod
    async def get_by_id(self, contract_id: uuid.UUID) -> DataContract | None: ...

    @abstractmethod
    async def list(self) -> list[DataContract]: ...

    @abstractmethod
    async def update(
        self,
        contract_id: uuid.UUID,
        title: str,
        version: str,
        owner: str,
        domain: str,
        tier: int,
        status: str,
        models: dict[str, Any],
        servicelevels: dict[str, Any],
    ) -> DataContract | None: ...

    @abstractmethod
    async def delete(self, contract_id: uuid.UUID) -> bool: ...
