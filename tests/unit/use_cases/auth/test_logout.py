import uuid
from unittest.mock import AsyncMock

import jwt
import pytest
from fastapi import HTTPException

from backend.interface.security import create_refresh_token
from backend.use_cases.auth.logout import LogoutUseCase

SECRET = "testsecret"


async def test_logout_revokes_token():
    jti = str(uuid.uuid4())
    raw_token = create_refresh_token(jti=jti, user_id="user-1", secret_key=SECRET, expire_days=7)
    token_repo = AsyncMock()
    await LogoutUseCase(token_repo=token_repo, secret_key=SECRET).execute(refresh_token=raw_token)
    token_repo.revoke.assert_awaited_once_with(uuid.UUID(jti))


async def test_logout_raises_401_on_invalid_token():
    token_repo = AsyncMock()
    with pytest.raises(HTTPException) as exc:
        await LogoutUseCase(token_repo=token_repo, secret_key=SECRET).execute(refresh_token="not.a.valid.token")
    assert exc.value.status_code == 401


async def test_logout_raises_401_when_token_has_no_jti():
    # Valid JWT signature but no jti claim — tests the `if not jti:` guard
    token_without_jti = jwt.encode({"sub": "user-1"}, SECRET, algorithm="HS256")
    token_repo = AsyncMock()
    with pytest.raises(HTTPException) as exc:
        await LogoutUseCase(token_repo=token_repo, secret_key=SECRET).execute(refresh_token=token_without_jti)
    assert exc.value.status_code == 401
