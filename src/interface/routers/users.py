from fastapi import APIRouter, HTTPException

from src.use_cases import create_user_interactor

router = APIRouter()


@router.post("/users", response_model=UserResponseModel)
async def create_user(user: UserCreateModel):
    try:
        created_user = await create_user_interactor(user)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    else:
        return created_user
