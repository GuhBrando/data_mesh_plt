import json
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from backend.infra.github_client import GitHubClient


def _resp(status: int, json_body: dict | None = None) -> MagicMock:
    r = MagicMock(spec=httpx.Response)
    r.status_code = status
    r.is_success = 200 <= status < 300
    body = json_body if json_body is not None else {}
    r.json.return_value = body
    r.text = json.dumps(body)
    return r


@pytest.fixture
def client():
    return GitHubClient(token="t", repo="acme/contracts")


def _async_client_ctx(mock_client):
    ctx = MagicMock()
    ctx.__aenter__ = AsyncMock(return_value=mock_client)
    ctx.__aexit__ = AsyncMock(return_value=False)
    return ctx


async def test_create_product_repo_user_owner_posts_to_user_repos(client):
    mock_http = AsyncMock()
    mock_http.get = AsyncMock(
        return_value=_resp(200, {"type": "User", "login": "acme"})
    )
    mock_http.post = AsyncMock(
        return_value=_resp(
            201, {"html_url": "https://github.com/acme/dp-x", "full_name": "acme/dp-x"}
        )
    )
    with patch(
        "backend.infra.github_client.httpx.AsyncClient",
        return_value=_async_client_ctx(mock_http),
    ):
        result = await client.create_product_repo("dp-x", "desc")
    assert result["html_url"] == "https://github.com/acme/dp-x"
    assert result["full_name"] == "acme/dp-x"
    mock_http.post.assert_awaited_once()
    posted_url = mock_http.post.await_args.args[0]
    assert posted_url.endswith("/user/repos")


async def test_create_product_repo_org_owner_posts_to_orgs_repos(client):
    mock_http = AsyncMock()
    mock_http.get = AsyncMock(
        return_value=_resp(200, {"type": "Organization", "login": "acme"})
    )
    mock_http.post = AsyncMock(
        return_value=_resp(
            201, {"html_url": "https://github.com/acme/dp-x", "full_name": "acme/dp-x"}
        )
    )
    with patch(
        "backend.infra.github_client.httpx.AsyncClient",
        return_value=_async_client_ctx(mock_http),
    ):
        await client.create_product_repo("dp-x", "desc")
    posted_url = mock_http.post.await_args.args[0]
    assert posted_url.endswith("/orgs/acme/repos")


async def test_create_product_repo_owner_type_cached(client):
    mock_http = AsyncMock()
    mock_http.get = AsyncMock(
        return_value=_resp(200, {"type": "User", "login": "acme"})
    )
    mock_http.post = AsyncMock(
        return_value=_resp(
            201, {"html_url": "https://github.com/acme/dp-x", "full_name": "acme/dp-x"}
        )
    )
    with patch(
        "backend.infra.github_client.httpx.AsyncClient",
        return_value=_async_client_ctx(mock_http),
    ):
        await client.create_product_repo("dp-x", "desc")
        await client.create_product_repo("dp-y", "desc")
    # Owner-detection GET should happen only once across both calls.
    assert mock_http.get.await_count == 1


async def test_create_product_repo_adopts_existing_on_422(client):
    mock_http = AsyncMock()
    mock_http.get = AsyncMock(
        side_effect=[
            _resp(200, {"type": "User", "login": "acme"}),
            _resp(
                200,
                {"html_url": "https://github.com/acme/dp-x", "full_name": "acme/dp-x"},
            ),
        ]
    )
    mock_http.post = AsyncMock(
        return_value=_resp(422, {"errors": [{"message": "name already exists"}]})
    )
    with patch(
        "backend.infra.github_client.httpx.AsyncClient",
        return_value=_async_client_ctx(mock_http),
    ):
        result = await client.create_product_repo("dp-x", "desc")
    assert result["full_name"] == "acme/dp-x"


async def test_create_product_repo_raises_on_other_failure(client):
    mock_http = AsyncMock()
    mock_http.get = AsyncMock(
        return_value=_resp(200, {"type": "User", "login": "acme"})
    )
    mock_http.post = AsyncMock(return_value=_resp(500, {"message": "boom"}))
    with patch(
        "backend.infra.github_client.httpx.AsyncClient",
        return_value=_async_client_ctx(mock_http),
    ):
        with pytest.raises(RuntimeError):
            await client.create_product_repo("dp-x", "desc")
