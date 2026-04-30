import uuid
from typing import List

import bcrypt
from fastapi import APIRouter, Depends, HTTPException

from backend.domain.entities.user import User
from backend.domain.value_objects.user_role import UserRole
from backend.infra.postgres import get_db_connection
from backend.infra.repositories.user_repository import PostgresUserRepository
from backend.interface.dependencies import (
    get_assign_role_use_case,
    get_create_user_use_case,
    get_delete_user_use_case,
    get_get_user_use_case,
    get_list_users_use_case,
    get_update_user_use_case,
    get_user_repository,
)
from backend.interface.permissions import require_roles
from backend.interface.schemas.domain import DomainResponseModel, RoleAssignModel
from backend.interface.schemas.user import (
    ChangePasswordModel,
    UserCreateModel,
    UserResponseModel,
    UserUpdateModel,
)
from backend.interface.security import get_current_user
from backend.use_cases.user.assign_role import AssignRoleUseCase
from backend.use_cases.user.create import CreateUserUseCase
from backend.use_cases.user.delete import DeleteUserUseCase
from backend.use_cases.user.get import GetUserUseCase
from backend.use_cases.user.list import ListUsersUseCase
from backend.use_cases.user.update import UpdateUserUseCase

router = APIRouter()


def _to_response(user: User) -> UserResponseModel:
    return UserResponseModel(
        id=user.id, username=user.name, email=str(user.email), role=user.role
    )


@router.post("/users", response_model=UserResponseModel, status_code=201)
async def create_user(
    body: UserCreateModel,
    use_case: CreateUserUseCase = Depends(get_create_user_use_case),
):
    try:
        user = await use_case.execute(
            name=body.username, email=body.email, password=body.password
        )
        return _to_response(user)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/users", response_model=List[UserResponseModel])
async def list_users(
    use_case: ListUsersUseCase = Depends(get_list_users_use_case),
    _: User = Depends(get_current_user),
):
    users = await use_case.execute()
    return [_to_response(u) for u in users]


@router.get("/users/{user_id}", response_model=UserResponseModel)
async def get_user(
    user_id: uuid.UUID,
    use_case: GetUserUseCase = Depends(get_get_user_use_case),
    _: User = Depends(get_current_user),
):
    user = await use_case.execute(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return _to_response(user)


@router.put("/users/{user_id}", response_model=UserResponseModel)
async def update_user(
    user_id: uuid.UUID,
    body: UserUpdateModel,
    use_case: UpdateUserUseCase = Depends(get_update_user_use_case),
    _: User = Depends(get_current_user),
):
    try:
        user = await use_case.execute(
            user_id=user_id, name=body.username, email=body.email
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return _to_response(user)


@router.delete("/users/{user_id}", status_code=204)
async def delete_user(
    user_id: uuid.UUID,
    use_case: DeleteUserUseCase = Depends(get_delete_user_use_case),
    _: User = Depends(require_roles(UserRole.PLATFORM_ADMIN)),
):
    deleted = await use_case.execute(user_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="User not found")


@router.get("/users/{user_id}/domains", response_model=List[DomainResponseModel])
async def get_user_domains(
    user_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db=Depends(get_db_connection),
):
    if current_user.id != user_id and current_user.role != UserRole.PLATFORM_ADMIN:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    rows = await db.fetch(
        """
        SELECT p.id, p.name
        FROM iam.principals p
        JOIN iam.principal_memberships pm ON pm.principals_id = p.id
        WHERE pm.users_id = $1 AND p.type = 'GROUP'
        ORDER BY p.name;
        """,
        user_id,
    )
    return [DomainResponseModel(id=row["id"], name=row["name"]) for row in rows]


@router.patch("/users/{user_id}/password", status_code=204)
async def change_password(
    user_id: uuid.UUID,
    body: ChangePasswordModel,
    current_user: User = Depends(get_current_user),
    repo: PostgresUserRepository = Depends(get_user_repository),
):
    if current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    user = await repo.get_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if not bcrypt.checkpw(body.current_password.encode(), user.password_hash.encode()):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    new_hash = bcrypt.hashpw(body.new_password.encode(), bcrypt.gensalt()).decode()
    await repo.change_password(user_id, new_hash)


@router.patch("/users/{user_id}/role", response_model=UserResponseModel)
async def assign_user_role(
    user_id: uuid.UUID,
    body: RoleAssignModel,
    use_case: AssignRoleUseCase = Depends(get_assign_role_use_case),
    _: User = Depends(require_roles(UserRole.PLATFORM_ADMIN)),
):
    try:
        role = UserRole(body.role)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid role: {body.role}")
    user = await use_case.execute(user_id=user_id, role=role)
    return _to_response(user)
