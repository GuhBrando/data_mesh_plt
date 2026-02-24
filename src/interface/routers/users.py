from fastapi import APIRouter, HTTPException
from pydantic import BaseModel


from src.interface.schemas.user import UserCreateModel, UserResponseModel
from src.use_cases.user_interactor import CreateUserInteractor

router = APIRouter()


@router.post("/users", response_model=UserResponseModel)
async def create_user(user: UserCreateModel):
    try:
        created_user = await CreateUserInteractor(user).execute()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    else:
        return created_user
