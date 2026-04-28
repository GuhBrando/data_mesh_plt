import uuid

from fastapi import HTTPException

from backend.domain.entities.user import User
from backend.domain.interfaces.user_repository import IUserRepository
from backend.domain.value_objects.user_role import UserRole


class AssignRoleUseCase:
    def __init__(self, repository: IUserRepository):
        self.repository = repository

    async def execute(self, user_id: uuid.UUID, role: UserRole) -> User:
        user = await self.repository.assign_role(user_id, role)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return user
