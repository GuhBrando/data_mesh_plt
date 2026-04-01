import uuid

from src.domain.interfaces.user_repository import IUserRepository


class DeleteUserUseCase:
    def __init__(self, repository: IUserRepository):
        self.repository = repository

    async def execute(self, user_id: uuid.UUID) -> bool:
        return await self.repository.delete(user_id)
