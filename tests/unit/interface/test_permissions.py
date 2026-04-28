import uuid
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import HTTPException

from backend.domain.entities.user import User
from backend.domain.value_objects.email import Email
from backend.domain.value_objects.user_role import UserRole
from backend.interface.permissions import require_roles, is_domain_member


def _make_user(role: UserRole) -> User:
    return User(id=uuid.uuid4(), name="Alice", email=Email("alice@example.com"), role=role)


async def test_require_roles_passes_when_role_matches():
    user = _make_user(UserRole.PLATFORM_ADMIN)
    dep = require_roles(UserRole.PLATFORM_ADMIN)
    result = await dep(current_user=user)
    assert result is user


async def test_require_roles_raises_403_when_role_does_not_match():
    user = _make_user(UserRole.DATA_CONSUMER)
    dep = require_roles(UserRole.PLATFORM_ADMIN)
    with pytest.raises(HTTPException) as exc:
        await dep(current_user=user)
    assert exc.value.status_code == 403


async def test_require_roles_allows_any_of_multiple_roles():
    user = _make_user(UserRole.DATA_STEWARD)
    dep = require_roles(UserRole.PLATFORM_ADMIN, UserRole.DATA_STEWARD)
    result = await dep(current_user=user)
    assert result is user
