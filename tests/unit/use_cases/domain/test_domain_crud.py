import uuid
from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException

from backend.domain.entities.domain import Domain
from backend.use_cases.domain.delete import DeleteDomainUseCase
from backend.use_cases.domain.list import ListDomainsUseCase
from backend.use_cases.domain.update import UpdateDomainUseCase
from backend.use_cases.domain.update_member import UpdateDomainMemberUseCase


def _domain():
    return Domain(id=uuid.uuid4(), name="Sales")


# ── Delete ───────────────────────────────────────────────────────────────────


async def test_delete_domain_returns_true():
    repo = AsyncMock()
    repo.delete.return_value = True
    result = await DeleteDomainUseCase(repo).execute(uuid.uuid4())
    assert result is True


async def test_delete_domain_returns_false_when_not_found():
    repo = AsyncMock()
    repo.delete.return_value = False
    result = await DeleteDomainUseCase(repo).execute(uuid.uuid4())
    assert result is False


# ── List ─────────────────────────────────────────────────────────────────────


async def test_list_domains_returns_all():
    repo = AsyncMock()
    domains = [_domain(), _domain()]
    repo.list.return_value = domains
    result = await ListDomainsUseCase(repo).execute()
    assert result == domains


async def test_list_domains_returns_empty():
    repo = AsyncMock()
    repo.list.return_value = []
    result = await ListDomainsUseCase(repo).execute()
    assert result == []


# ── Update ───────────────────────────────────────────────────────────────────


async def test_update_domain_returns_updated():
    repo = AsyncMock()
    domain = _domain()
    repo.update.return_value = domain
    result = await UpdateDomainUseCase(repo).execute(
        domain_id=domain.id, name="Updated"
    )
    repo.update.assert_called_once_with(
        domain_id=domain.id, name="Updated", description=None, owner_id=None
    )
    assert result is domain


async def test_update_domain_returns_none_when_not_found():
    repo = AsyncMock()
    repo.update.return_value = None
    result = await UpdateDomainUseCase(repo).execute(domain_id=uuid.uuid4())
    assert result is None


# ── UpdateMember ─────────────────────────────────────────────────────────────


async def test_update_member_role_to_maintainer():
    from backend.domain.entities.domain import DomainMember

    repo = AsyncMock()
    domain_id = uuid.uuid4()
    user_id = uuid.uuid4()
    member = DomainMember(user_id=user_id, username="alice", role="maintainer")
    repo.update_member_role.return_value = member
    result = await UpdateDomainMemberUseCase(repo).execute(
        domain_id=domain_id, user_id=user_id, role="maintainer"
    )
    assert result.role == "maintainer"


async def test_update_member_role_to_member():
    from backend.domain.entities.domain import DomainMember

    repo = AsyncMock()
    domain_id = uuid.uuid4()
    user_id = uuid.uuid4()
    member = DomainMember(user_id=user_id, username="alice", role="member")
    repo.update_member_role.return_value = member
    result = await UpdateDomainMemberUseCase(repo).execute(
        domain_id=domain_id, user_id=user_id, role="member"
    )
    assert result.role == "member"


async def test_update_member_raises_400_on_invalid_role():
    repo = AsyncMock()
    with pytest.raises(HTTPException) as exc:
        await UpdateDomainMemberUseCase(repo).execute(
            domain_id=uuid.uuid4(), user_id=uuid.uuid4(), role="owner"
        )
    assert exc.value.status_code == 400


async def test_update_member_raises_404_when_member_not_found():
    repo = AsyncMock()
    repo.update_member_role.return_value = None
    with pytest.raises(HTTPException) as exc:
        await UpdateDomainMemberUseCase(repo).execute(
            domain_id=uuid.uuid4(), user_id=uuid.uuid4(), role="member"
        )
    assert exc.value.status_code == 404
