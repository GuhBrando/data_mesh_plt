from backend.domain.entities.user import User
from backend.domain.interfaces.user_repository import IUserRepository
from backend.domain.value_objects.email import Email


class CreateUserUseCase:
    def __init__(self, repository: IUserRepository):
        self.repository = repository

    async def execute(self, name: str, email: str) -> User:
        Email(email)  # raises ValueError if invalid
        return await self.repository.create(name=name, email=email)
