from fastapi import APIRouter, HTTPException

from src.domain import user_persistence

router = APIRouter()


@router.post("/users", response_model=UserResponseModel)
async def create_user(user: UserCreateModel):
    try:
        created_user = await user_persistence(user)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    else:
        return created_user
