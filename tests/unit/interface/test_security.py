import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

from backend.interface.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    get_current_user,
)


def test_create_access_token_returns_string():
    token = create_access_token(user_id="test-user-id", secret_key="testsecret", expire_minutes=15)
    assert isinstance(token, str)
    assert len(token) > 0


def test_decode_token_returns_correct_sub():
    token = create_access_token(user_id="user-123", secret_key="testsecret", expire_minutes=15)
    payload = decode_token(token, secret_key="testsecret")
    assert payload["sub"] == "user-123"


def test_decode_token_raises_on_expired():
    from fastapi import HTTPException
    token = create_access_token(user_id="user-123", secret_key="testsecret", expire_minutes=-1)
    with pytest.raises(HTTPException) as exc:
        decode_token(token, secret_key="testsecret")
    assert exc.value.status_code == 401
    assert "expired" in exc.value.detail.lower()


def test_decode_token_raises_on_invalid():
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc:
        decode_token("not.a.valid.token", secret_key="testsecret")
    assert exc.value.status_code == 401


def test_create_refresh_token_contains_jti():
    jti = str(uuid.uuid4())
    token = create_refresh_token(
        jti=jti, user_id="user-123", secret_key="testsecret", expire_days=7
    )
    payload = decode_token(token, secret_key="testsecret")
    assert payload["jti"] == jti
    assert payload["sub"] == "user-123"


# ── get_current_user ─────────────────────────────────────────────────────────


async def test_get_current_user_returns_user():
    user_id = uuid.uuid4()
    mock_user = MagicMock()
    mock_repo = AsyncMock()
    mock_repo.get_by_id.return_value = mock_user
    credentials = MagicMock()
    credentials.credentials = "token"

    with patch(
        "backend.interface.security.decode_token",
        return_value={"sub": str(user_id)},
    ), patch(
        "backend.infra.repositories.user_repository.PostgresUserRepository",
        return_value=mock_repo,
    ):
        result = await get_current_user(credentials=credentials, db=None)

    assert result is mock_user


async def test_get_current_user_raises_401_when_no_sub():
    credentials = MagicMock()
    credentials.credentials = "token"

    with patch(
        "backend.interface.security.decode_token",
        return_value={},
    ):
        with pytest.raises(HTTPException) as exc:
            await get_current_user(credentials=credentials, db=None)

    assert exc.value.status_code == 401


async def test_get_current_user_raises_401_when_user_not_found():
    user_id = uuid.uuid4()
    mock_repo = AsyncMock()
    mock_repo.get_by_id.return_value = None
    credentials = MagicMock()
    credentials.credentials = "token"

    with patch(
        "backend.interface.security.decode_token",
        return_value={"sub": str(user_id)},
    ), patch(
        "backend.infra.repositories.user_repository.PostgresUserRepository",
        return_value=mock_repo,
    ):
        with pytest.raises(HTTPException) as exc:
            await get_current_user(credentials=credentials, db=None)

    assert exc.value.status_code == 401
