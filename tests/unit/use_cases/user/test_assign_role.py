import uuid
from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException

from backend.domain.entities.user import User
from backend.domain.value_objects.email import Email
from backend.domain.value_objects.user_role import UserRole
from backend.use_cases.user.assign_role import AssignRoleUseCase


def test_user_defaults_to_data_consumer():
    user = User(id=uuid.uuid4(), name="Alice", email=Email("alice@example.com"))
    assert user.role == UserRole.DATA_CONSUMER


def test_user_can_be_created_with_explicit_role():
    user = User(
        id=uuid.uuid4(),
        name="Bob",
        email=Email("bob@example.com"),
        role=UserRole.PLATFORM_ADMIN,
    )
    assert user.role == UserRole.PLATFORM_ADMIN


async def test_assign_role_returns_updated_user():
    user_id = uuid.uuid4()
    updated = User(id=user_id, name="Alice", email=Email("alice@example.com"), role=UserRole.DATA_STEWARD)
    repo = AsyncMock()
    repo.assign_role.return_value = updated
    token_repo = AsyncMock()
    use_case = AssignRoleUseCase(repo, token_repo)
    result = await use_case.execute(user_id=user_id, role=UserRole.DATA_STEWARD)
    repo.assign_role.assert_called_once_with(user_id, UserRole.DATA_STEWARD)
    token_repo.revoke_all_for_user.assert_called_once_with(user_id)
    assert result.role == UserRole.DATA_STEWARD


async def test_assign_role_raises_404_when_user_not_found():
    repo = AsyncMock()
    repo.assign_role.return_value = None
    token_repo = AsyncMock()
    use_case = AssignRoleUseCase(repo, token_repo)
    with pytest.raises(HTTPException) as exc:
        await use_case.execute(user_id=uuid.uuid4(), role=UserRole.DATA_OWNER)
    assert exc.value.status_code == 404
