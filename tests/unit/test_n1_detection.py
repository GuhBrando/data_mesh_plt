from unittest.mock import AsyncMock

import pytest

from backend.use_cases.data_product.list import ListDataProductsUseCase


@pytest.mark.n1
async def test_list_data_products_makes_single_db_call(n1_guard):
    repo = AsyncMock()
    repo.list.return_value = []

    guard = n1_guard(repo)
    use_case = ListDataProductsUseCase(repository=repo)
    await use_case.execute()

    guard.assert_max_calls("list", max_calls=1)


@pytest.mark.n1
async def test_n1_guard_catches_repeated_calls(n1_guard):
    """Self-test: verify the guard correctly detects repeated calls."""
    repo = AsyncMock()
    guard = n1_guard(repo)

    for _ in range(3):
        await repo.get()

    with pytest.raises(AssertionError, match="N\\+1 detected"):
        guard.assert_max_calls("get", max_calls=1)
