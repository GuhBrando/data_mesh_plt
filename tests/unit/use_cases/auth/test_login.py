import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock

import bcrypt
import pytest
from fastapi import HTTPException

from backend.domain.entities.refresh_token import RefreshToken
from backend.domain.entities.user import User
from backend.domain.value_objects.email import Email
from backend.use_cases.auth.login import LoginUseCase


def _make_user(password: str) -> User:
    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    return User(id=uuid.uuid4(), name="Alice", email=Email("alice@example.com"), password_hash=hashed)


def _make_token_repo() -> AsyncMock:
    repo = AsyncMock()
    repo.create.return_value = RefreshToken(
        id=uuid.uuid4(), user_id=uuid.uuid4(), token_hash="hash",
        expires_at=datetime.now(timezone.utc), revoked=False,
    )
    return repo


async def test_login_returns_tokens_on_valid_credentials():
    user = _make_user("Str0ng!Pass")
    user_repo = AsyncMock()
    user_repo.get_by_email.return_value = user
    use_case = LoginUseCase(user_repo=user_repo, token_repo=_make_token_repo())
    result = await use_case.execute(email="alice@example.com", password="Str0ng!Pass")
    assert "access_token" in result
    assert "refresh_token" in result
    assert result["token_type"] == "bearer"


async def test_login_raises_401_on_wrong_password():
    user = _make_user("Str0ng!Pass")
    user_repo = AsyncMock()
    user_repo.get_by_email.return_value = user
    use_case = LoginUseCase(user_repo=user_repo, token_repo=_make_token_repo())
    with pytest.raises(HTTPException) as exc:
        await use_case.execute(email="alice@example.com", password="WrongPass1!")
    assert exc.value.status_code == 401
    assert exc.value.detail == "Invalid credentials"


async def test_login_raises_401_on_unknown_email():
    user_repo = AsyncMock()
    user_repo.get_by_email.return_value = None
    use_case = LoginUseCase(user_repo=user_repo, token_repo=_make_token_repo())
    with pytest.raises(HTTPException) as exc:
        await use_case.execute(email="nobody@example.com", password="Str0ng!Pass")
    assert exc.value.status_code == 401
    assert exc.value.detail == "Invalid credentials"
