import uuid
from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException

from backend.domain.entities.domain import Domain
from backend.use_cases.domain.create import CreateDomainUseCase


async def test_create_domain_returns_domain():
    domain = Domain(id=uuid.uuid4(), name="Sales")
    repo = AsyncMock()
    repo.create.return_value = domain
    use_case = CreateDomainUseCase(repo)
    result = await use_case.execute(name="Sales")
    repo.create.assert_called_once_with("Sales")
    assert result.name == "Sales"


async def test_create_domain_raises_on_empty_name():
    use_case = CreateDomainUseCase(AsyncMock())
    with pytest.raises(HTTPException) as exc:
        await use_case.execute(name="")
    assert exc.value.status_code == 400


async def test_create_domain_raises_on_whitespace_only_name():
    use_case = CreateDomainUseCase(AsyncMock())
    with pytest.raises(HTTPException) as exc:
        await use_case.execute(name="   ")
    assert exc.value.status_code == 400


async def test_create_domain_strips_surrounding_whitespace():
    domain = Domain(id=uuid.uuid4(), name="Finance")
    repo = AsyncMock()
    repo.create.return_value = domain
    use_case = CreateDomainUseCase(repo)
    await use_case.execute(name="  Finance  ")
    repo.create.assert_called_once_with("Finance")
