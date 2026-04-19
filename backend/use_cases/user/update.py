import uuid

from backend.domain.entities.user import User
from backend.domain.interfaces.user_repository import IUserRepository
from backend.domain.value_objects.email import Email


class UpdateUserUseCase:
    def __init__(self, repository: IUserRepository):
        self.repository = repository

    async def execute(
        self, user_id: uuid.UUID, name: str | None, email: str | None
    ) -> User | None:
        if email is not None:
            Email(email)  # raises ValueError if invalid
        return await self.repository.update(user_id=user_id, name=name, email=email)
