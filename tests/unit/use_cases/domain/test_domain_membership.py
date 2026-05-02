import uuid
from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException

from backend.use_cases.domain.add_member import AddDomainMemberUseCase
from backend.use_cases.domain.remove_member import RemoveDomainMemberUseCase


async def test_add_member_calls_repo():
    repo = AsyncMock()
    repo.get_by_id.return_value = object()
    use_case = AddDomainMemberUseCase(repo)
    await use_case.execute(domain_id=uuid.uuid4(), user_id=uuid.uuid4())
    repo.add_member.assert_called_once()


async def test_add_member_passes_correct_ids_to_repo():
    domain_id = uuid.uuid4()
    user_id = uuid.uuid4()
    repo = AsyncMock()
    repo.get_by_id.return_value = object()
    await AddDomainMemberUseCase(repo).execute(domain_id=domain_id, user_id=user_id)
    repo.add_member.assert_called_once_with(domain_id=domain_id, user_id=user_id)


async def test_add_member_raises_404_when_domain_not_found():
    repo = AsyncMock()
    repo.get_by_id.return_value = None
    use_case = AddDomainMemberUseCase(repo)
    with pytest.raises(HTTPException) as exc:
        await use_case.execute(domain_id=uuid.uuid4(), user_id=uuid.uuid4())
    assert exc.value.status_code == 404


async def test_remove_member_calls_repo():
    repo = AsyncMock()
    use_case = RemoveDomainMemberUseCase(repo)
    await use_case.execute(domain_id=uuid.uuid4(), user_id=uuid.uuid4())
    repo.remove_member.assert_called_once()
