from fastapi import APIRouter, HTTPException, Request

from src.interface.schemas.user import UserCreateModel, UserResponseModel
from src.use_cases.user_interactor import CreateUserInteractor

router = APIRouter()


@router.post("/users", response_model=UserResponseModel)
async def create_user(user: UserCreateModel, request: Request):
    try:
        body = await request.json()
        print("Incoming request body:", body)

        created_user = await CreateUserInteractor(user).execute()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    else:
        return created_user
