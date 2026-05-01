import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock

import pytest

from backend.domain.entities.data_contract import DataContract
from backend.use_cases.data_contract.create import CreateDataContractUseCase
from backend.use_cases.data_contract.update import UpdateDataContractUseCase

NOW = datetime.now(tz=timezone.utc)


def make_contract(**kwargs) -> DataContract:
    defaults = dict(
        id=uuid.uuid4(),
        title="T",
        version="1.0.0",
        owner="o",
        domain="d",
        tier=3,
        status="draft",
        models={"fields": []},
        servicelevels={"freshness": "", "availability": "", "retention": "", "latency": ""},
        created_at=NOW,
        updated_at=NOW,
    )
    return DataContract(**{**defaults, **kwargs})


@pytest.mark.asyncio
async def test_create_calls_repository():
    repo = AsyncMock()
    repo.create.return_value = make_contract(title="Orders")
    use_case = CreateDataContractUseCase(repo)

    result = await use_case.execute(
        title="Orders", version="1.0.0", owner="alice", domain="commerce",
        tier=2, status="draft", models={"fields": []},
        servicelevels={"freshness": "24h", "availability": "", "retention": "", "latency": ""},
    )

    repo.create.assert_called_once()
    assert result.title == "Orders"


@pytest.mark.asyncio
async def test_create_raises_on_empty_title():
    repo = AsyncMock()
    use_case = CreateDataContractUseCase(repo)

    with pytest.raises(ValueError, match="title"):
        await use_case.execute(
            title="", version="1.0.0", owner="alice", domain="commerce",
            tier=2, status="draft", models={"fields": []},
            servicelevels={"freshness": "", "availability": "", "retention": "", "latency": ""},
        )


@pytest.mark.asyncio
async def test_update_calls_repository():
    repo = AsyncMock()
    cid = uuid.uuid4()
    repo.update.return_value = make_contract(title="Updated")
    use_case = UpdateDataContractUseCase(repo)

    result = await use_case.execute(
        contract_id=cid,
        title="Updated", version="1.0.0", owner="bob", domain="finance",
        tier=1, status="in_review", models={"fields": []},
        servicelevels={"freshness": "1h", "availability": "99.9%", "retention": "365d", "latency": "30m"},
    )

    repo.update.assert_called_once()
    assert result.title == "Updated"


@pytest.mark.asyncio
async def test_update_raises_on_empty_title():
    repo = AsyncMock()
    use_case = UpdateDataContractUseCase(repo)
    with pytest.raises(ValueError, match="title"):
        await use_case.execute(
            contract_id=uuid.uuid4(),
            title="", version="1.0.0", owner="alice", domain="commerce",
            tier=2, status="draft", models={"fields": []},
            servicelevels={"freshness": "", "availability": "", "retention": "", "latency": ""},
        )


@pytest.mark.asyncio
async def test_create_passes_title_to_repo():
    repo = AsyncMock()
    repo.create.return_value = make_contract(title="Inventory")
    await CreateDataContractUseCase(repo).execute(
        title="Inventory", version="1.0.0", owner="alice", domain="ops",
        tier=3, status="draft", models={"fields": []},
        servicelevels={"freshness": "", "availability": "", "retention": "", "latency": ""},
    )
    assert repo.create.call_args.kwargs["title"] == "Inventory"


@pytest.mark.asyncio
async def test_update_passes_title_to_repo():
    repo = AsyncMock()
    repo.update.return_value = make_contract(title="NewName")
    await UpdateDataContractUseCase(repo).execute(
        contract_id=uuid.uuid4(),
        title="NewName", version="1.0.0", owner="bob", domain="finance",
        tier=2, status="draft", models={"fields": []},
        servicelevels={"freshness": "", "availability": "", "retention": "", "latency": ""},
    )
    assert repo.update.call_args.kwargs["title"] == "NewName"
