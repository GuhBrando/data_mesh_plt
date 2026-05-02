import hashlib
import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock

import jwt
import pytest
from fastapi import HTTPException

from backend.domain.entities.refresh_token import RefreshToken
from backend.interface.security import create_refresh_token
from backend.use_cases.auth.refresh import RefreshUseCase

SECRET = "testsecret"


def _make_stored_token(raw_token: str, revoked: bool = False) -> RefreshToken:
    return RefreshToken(
        id=uuid.uuid4(), user_id=uuid.uuid4(),
        token_hash=hashlib.sha256(raw_token.encode()).hexdigest(),
        expires_at=datetime.now(timezone.utc), revoked=revoked,
    )


async def test_refresh_returns_new_access_token():
    jti = str(uuid.uuid4())
    raw_token = create_refresh_token(jti=jti, user_id="user-1", secret_key=SECRET, expire_days=7)
    stored = _make_stored_token(raw_token)
    stored.id = uuid.UUID(jti)
    token_repo = AsyncMock()
    token_repo.get_by_id.return_value = stored
    result = await RefreshUseCase(token_repo=token_repo, secret_key=SECRET).execute(refresh_token=raw_token)
    assert "access_token" in result
    assert result["token_type"] == "bearer"


async def test_refresh_raises_401_on_revoked_token():
    jti = str(uuid.uuid4())
    raw_token = create_refresh_token(jti=jti, user_id="user-1", secret_key=SECRET, expire_days=7)
    stored = _make_stored_token(raw_token, revoked=True)
    stored.id = uuid.UUID(jti)
    token_repo = AsyncMock()
    token_repo.get_by_id.return_value = stored
    with pytest.raises(HTTPException) as exc:
        await RefreshUseCase(token_repo=token_repo, secret_key=SECRET).execute(refresh_token=raw_token)
    assert exc.value.status_code == 401


async def test_refresh_raises_401_on_tampered_token():
    jti = str(uuid.uuid4())
    raw_token = create_refresh_token(jti=jti, user_id="user-1", secret_key=SECRET, expire_days=7)
    stored = _make_stored_token("different_token")
    stored.id = uuid.UUID(jti)
    token_repo = AsyncMock()
    token_repo.get_by_id.return_value = stored
    with pytest.raises(HTTPException) as exc:
        await RefreshUseCase(token_repo=token_repo, secret_key=SECRET).execute(refresh_token=raw_token)
    assert exc.value.status_code == 401


async def test_refresh_raises_401_when_token_not_in_repo():
    jti = str(uuid.uuid4())
    raw_token = create_refresh_token(jti=jti, user_id="user-1", secret_key=SECRET, expire_days=7)
    token_repo = AsyncMock()
    token_repo.get_by_id.return_value = None
    with pytest.raises(HTTPException) as exc:
        await RefreshUseCase(token_repo=token_repo, secret_key=SECRET).execute(refresh_token=raw_token)
    assert exc.value.status_code == 401


async def test_refresh_raises_401_when_payload_missing_jti():
    # Valid JWT but no jti — tests the `if not jti or not user_id:` guard
    token_no_jti = jwt.encode({"sub": "user-1"}, SECRET, algorithm="HS256")
    token_repo = AsyncMock()
    with pytest.raises(HTTPException) as exc:
        await RefreshUseCase(token_repo=token_repo, secret_key=SECRET).execute(refresh_token=token_no_jti)
    assert exc.value.status_code == 401


async def test_refresh_raises_401_when_payload_missing_user_id():
    # Valid JWT but no sub — tests the `not user_id` part of the guard
    token_no_sub = jwt.encode({"jti": str(uuid.uuid4())}, SECRET, algorithm="HS256")
    token_repo = AsyncMock()
    with pytest.raises(HTTPException) as exc:
        await RefreshUseCase(token_repo=token_repo, secret_key=SECRET).execute(refresh_token=token_no_sub)
    assert exc.value.status_code == 401
