import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException

from src.domain.entities.user import User
from src.interface.dependencies import (
    get_create_user_use_case,
    get_delete_user_use_case,
    get_get_user_use_case,
    get_list_users_use_case,
    get_update_user_use_case,
)
from src.interface.schemas.user import (
    UserCreateModel,
    UserResponseModel,
    UserUpdateModel,
)
from src.use_cases.user.create import CreateUserUseCase
from src.use_cases.user.delete import DeleteUserUseCase
from src.use_cases.user.get import GetUserUseCase
from src.use_cases.user.list import ListUsersUseCase
from src.use_cases.user.update import UpdateUserUseCase

router = APIRouter()


def _to_response(user: User) -> UserResponseModel:
    return UserResponseModel(id=user.id, username=user.name, email=str(user.email))


@router.post("/users", response_model=UserResponseModel, status_code=201)
async def create_user(
    body: UserCreateModel,
    use_case: CreateUserUseCase = Depends(get_create_user_use_case),
):
    try:
        user = await use_case.execute(name=body.username, email=body.email)
        return _to_response(user)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/users", response_model=List[UserResponseModel])
async def list_users(use_case: ListUsersUseCase = Depends(get_list_users_use_case)):
    users = await use_case.execute()
    return [_to_response(u) for u in users]


@router.get("/users/{user_id}", response_model=UserResponseModel)
async def get_user(
    user_id: uuid.UUID,
    use_case: GetUserUseCase = Depends(get_get_user_use_case),
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
):
    deleted = await use_case.execute(user_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="User not found")
