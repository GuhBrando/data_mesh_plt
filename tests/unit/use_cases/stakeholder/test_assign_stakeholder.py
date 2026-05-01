import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException

from backend.domain.entities.contract_stakeholder import ContractStakeholder
from backend.use_cases.stakeholder.assign import AssignStakeholderUseCase
from backend.use_cases.stakeholder.remove import RemoveStakeholderUseCase


def _make_stakeholder(contract_id, user_id, assigned_by) -> ContractStakeholder:
    return ContractStakeholder(
        contract_id=contract_id,
        user_id=user_id,
        assigned_by=assigned_by,
        assigned_at=datetime.now(timezone.utc),
    )


async def test_assign_stakeholder_returns_stakeholder():
    contract_id = uuid.uuid4()
    user_id = uuid.uuid4()
    assigned_by = uuid.uuid4()
    stakeholder = _make_stakeholder(contract_id, user_id, assigned_by)
    repo = AsyncMock()
    repo.assign.return_value = stakeholder
    use_case = AssignStakeholderUseCase(repo)
    result = await use_case.execute(
        contract_id=contract_id, user_id=user_id, assigned_by=assigned_by
    )
    repo.assign.assert_called_once_with(contract_id, user_id, assigned_by)
    assert result.user_id == user_id


async def test_remove_stakeholder_raises_404_when_not_found():
    repo = AsyncMock()
    repo.remove.return_value = False
    use_case = RemoveStakeholderUseCase(repo)
    with pytest.raises(HTTPException) as exc:
        await use_case.execute(contract_id=uuid.uuid4(), user_id=uuid.uuid4())
    assert exc.value.status_code == 404


async def test_remove_stakeholder_succeeds():
    repo = AsyncMock()
    repo.remove.return_value = True
    use_case = RemoveStakeholderUseCase(repo)
    await use_case.execute(contract_id=uuid.uuid4(), user_id=uuid.uuid4())
    repo.remove.assert_called_once()


async def test_remove_stakeholder_passes_correct_ids_to_repo():
    contract_id = uuid.uuid4()
    user_id = uuid.uuid4()
    repo = AsyncMock()
    repo.remove.return_value = True
    await RemoveStakeholderUseCase(repo).execute(contract_id=contract_id, user_id=user_id)
    repo.remove.assert_called_once_with(contract_id, user_id)
