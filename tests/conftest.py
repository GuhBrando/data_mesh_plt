from collections.abc import Callable
from unittest.mock import AsyncMock

import pytest


class _QueryGuard:
    def __init__(self, mock: AsyncMock) -> None:
        self._mock = mock

    def assert_max_calls(self, method_name: str, max_calls: int = 1) -> None:
        method = getattr(self._mock, method_name)
        count = method.call_count
        if count > max_calls:
            raise AssertionError(
                f"N+1 detected: '{method_name}' called {count} times "
                f"(max allowed: {max_calls})"
            )


@pytest.fixture
def n1_guard() -> Callable[[AsyncMock], _QueryGuard]:
    def _make(mock: AsyncMock) -> _QueryGuard:
        return _QueryGuard(mock)

    return _make
