from src.domain.entities.user import User
from src.domain.interfaces.user_repository import IUserRepository


class ListUsersUseCase:
    def __init__(self, repository: IUserRepository):
        self.repository = repository

    async def execute(self) -> list[User]:
        return await self.repository.list()
