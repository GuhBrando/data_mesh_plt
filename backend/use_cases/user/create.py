import bcrypt

from backend.domain.entities.user import User
from backend.domain.interfaces.user_repository import IUserRepository
from backend.domain.value_objects.email import Email


class CreateUserUseCase:
    def __init__(self, repository: IUserRepository):
        self.repository = repository

    async def execute(self, name: str, email: str, password: str) -> User:
        Email(email)  # raises ValueError if invalid
        password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
        return await self.repository.create(
            name=name, email=email, password_hash=password_hash
        )
