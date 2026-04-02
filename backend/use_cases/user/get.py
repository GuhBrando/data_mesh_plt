import uuid

from backend.domain.entities.user import User
from backend.domain.interfaces.user_repository import IUserRepository


class GetUserUseCase:
    def __init__(self, repository: IUserRepository):
        self.repository = repository

    async def execute(self, user_id: uuid.UUID) -> User | None:
        return await self.repository.get_by_id(user_id)
