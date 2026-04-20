import uuid
from datetime import UTC, datetime, timedelta

import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from backend.infra.config import (
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES,
    JWT_REFRESH_TOKEN_EXPIRE_DAYS,
    JWT_SECRET_KEY,
)
from backend.infra.postgres import get_db_connection

ALGORITHM = "HS256"
bearer_scheme = HTTPBearer()


def create_access_token(
    user_id: str,
    secret_key: str = JWT_SECRET_KEY,
    expire_minutes: int = JWT_ACCESS_TOKEN_EXPIRE_MINUTES,
) -> str:
    expire = datetime.now(UTC) + timedelta(minutes=expire_minutes)
    return jwt.encode({"sub": user_id, "exp": expire}, secret_key, algorithm=ALGORITHM)


def create_refresh_token(
    jti: str,
    user_id: str,
    secret_key: str = JWT_SECRET_KEY,
    expire_days: int = JWT_REFRESH_TOKEN_EXPIRE_DAYS,
) -> str:
    expire = datetime.now(UTC) + timedelta(days=expire_days)
    return jwt.encode(
        {"sub": user_id, "jti": jti, "exp": expire}, secret_key, algorithm=ALGORITHM
    )


def decode_token(token: str, secret_key: str = JWT_SECRET_KEY) -> dict:
    try:
        return jwt.decode(token, secret_key, algorithms=[ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Could not validate credentials")


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db=Depends(get_db_connection),
):
    from backend.infra.repositories.user_repository import PostgresUserRepository

    payload = decode_token(credentials.credentials)
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Could not validate credentials")
    repo = PostgresUserRepository(db)
    user = await repo.get_by_id(uuid.UUID(user_id))
    if not user:
        raise HTTPException(status_code=401, detail="Could not validate credentials")
    return user
