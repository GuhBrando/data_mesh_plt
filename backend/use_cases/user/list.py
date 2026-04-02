from backend.domain.entities.user import User
from backend.domain.interfaces.user_repository import IUserRepository


class ListUsersUseCase:
    def __init__(self, repository: IUserRepository):
        self.repository = repository

    async def execute(self) -> list[User]:
        return await self.repository.list()
