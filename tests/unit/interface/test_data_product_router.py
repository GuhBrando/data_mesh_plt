import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

from backend.domain.entities.data_product import DataProduct
from backend.domain.entities.user import User
from backend.domain.value_objects.email import Email
from backend.domain.value_objects.user_role import UserRole
from backend.infra.postgres import get_db_connection
from backend.interface.dependencies import (
    get_create_data_product_use_case,
    get_delete_data_product_use_case,
    get_get_data_product_use_case,
    get_list_data_products_use_case,
    get_update_data_product_use_case,
)
from backend.interface.security import get_current_user
from backend.main import app

NOW = datetime.now(tz=timezone.utc)
PRODUCT_ID = uuid.uuid4()
CONTRACT_ID = uuid.uuid4()
USER_ID = uuid.uuid4()


def _product(**kw) -> DataProduct:
    return DataProduct(
        id=kw.get("id", PRODUCT_ID),
        name=kw.get("name", "Orders Product"),
        description=kw.get("description", "desc"),
        data_contracts_id=kw.get("data_contracts_id", CONTRACT_ID),
        created_at=NOW,
        updated_at=NOW,
    )


def _admin() -> User:
    return User(
        id=USER_ID,
        name="Admin",
        email=Email("admin@example.com"),
        role=UserRole.PLATFORM_ADMIN,
    )


@pytest.fixture
def admin_client():
    mock_db = AsyncMock()
    app.dependency_overrides[get_current_user] = lambda: _admin()
    app.dependency_overrides[get_db_connection] = lambda: mock_db
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_create_data_product(admin_client):
    mock_uc = AsyncMock()
    mock_uc.execute.return_value = _product(name="Invoices Product")
    app.dependency_overrides[get_create_data_product_use_case] = lambda: mock_uc
    resp = admin_client.post(
        "/api/v1/data-products",
        json={
            "name": "Invoices Product",
            "description": "desc",
            "data_contracts_id": str(CONTRACT_ID),
        },
    )
    assert resp.status_code == 201
    assert resp.json()["name"] == "Invoices Product"


def test_list_data_products(admin_client):
    mock_uc = AsyncMock()
    mock_uc.execute.return_value = [_product(), _product(id=uuid.uuid4(), name="B")]
    app.dependency_overrides[get_list_data_products_use_case] = lambda: mock_uc
    resp = admin_client.get("/api/v1/data-products")
    assert resp.status_code == 200
    assert len(resp.json()) == 2


def test_list_data_products_empty(admin_client):
    mock_uc = AsyncMock()
    mock_uc.execute.return_value = []
    app.dependency_overrides[get_list_data_products_use_case] = lambda: mock_uc
    resp = admin_client.get("/api/v1/data-products")
    assert resp.status_code == 200
    assert resp.json() == []


def test_get_data_product_found(admin_client):
    mock_uc = AsyncMock()
    mock_uc.execute.return_value = _product()
    app.dependency_overrides[get_get_data_product_use_case] = lambda: mock_uc
    resp = admin_client.get(f"/api/v1/data-products/{PRODUCT_ID}")
    assert resp.status_code == 200
    assert resp.json()["name"] == "Orders Product"


def test_get_data_product_not_found(admin_client):
    mock_uc = AsyncMock()
    mock_uc.execute.return_value = None
    app.dependency_overrides[get_get_data_product_use_case] = lambda: mock_uc
    resp = admin_client.get(f"/api/v1/data-products/{uuid.uuid4()}")
    assert resp.status_code == 404


def test_update_data_product(admin_client):
    mock_uc = AsyncMock()
    mock_uc.execute.return_value = _product(name="Updated")
    app.dependency_overrides[get_update_data_product_use_case] = lambda: mock_uc
    resp = admin_client.put(
        f"/api/v1/data-products/{PRODUCT_ID}", json={"name": "Updated"}
    )
    assert resp.status_code == 200
    assert resp.json()["name"] == "Updated"


def test_update_data_product_not_found(admin_client):
    mock_uc = AsyncMock()
    mock_uc.execute.return_value = None
    app.dependency_overrides[get_update_data_product_use_case] = lambda: mock_uc
    resp = admin_client.put(
        f"/api/v1/data-products/{uuid.uuid4()}", json={"name": "X"}
    )
    assert resp.status_code == 404


def test_delete_data_product(admin_client):
    mock_uc = AsyncMock()
    mock_uc.execute.return_value = True
    app.dependency_overrides[get_delete_data_product_use_case] = lambda: mock_uc
    resp = admin_client.delete(f"/api/v1/data-products/{PRODUCT_ID}")
    assert resp.status_code == 204


def test_delete_data_product_not_found(admin_client):
    mock_uc = AsyncMock()
    mock_uc.execute.return_value = False
    app.dependency_overrides[get_delete_data_product_use_case] = lambda: mock_uc
    resp = admin_client.delete(f"/api/v1/data-products/{uuid.uuid4()}")
    assert resp.status_code == 404


def test_get_data_product_includes_repo_url(admin_client):
    mock_uc = AsyncMock()
    mock_uc.execute.return_value = _product()
    mock_uc.execute.return_value.repo_url = "https://github.com/acme/dp-x"
    app.dependency_overrides[get_get_data_product_use_case] = lambda: mock_uc
    resp = admin_client.get(f"/api/v1/data-products/{PRODUCT_ID}")
    assert resp.status_code == 200
    assert resp.json()["repo_url"] == "https://github.com/acme/dp-x"


from unittest.mock import patch as _patch  # noqa: E402, F401

from backend.interface.dependencies import (  # noqa: E402
    get_data_contract_repository,
    get_data_product_repository,
    get_github_client,
)


class _StubContract:
    def __init__(self, domain: str = "Marketing"):
        self.domain = domain


def test_create_data_product_triggers_repo_provisioning(admin_client):
    mock_uc = AsyncMock()
    mock_uc.execute.return_value = _product(name="Attribution Model")
    mock_github = AsyncMock()
    mock_github.create_product_repo.return_value = {
        "html_url": "https://github.com/acme/dp-marketing-attribution-model",
        "full_name": "acme/dp-marketing-attribution-model",
    }
    mock_github.push_scaffold = AsyncMock()
    mock_contract_repo = AsyncMock()
    mock_contract_repo.get_by_id.return_value = _StubContract("Marketing")
    mock_product_repo = AsyncMock()

    app.dependency_overrides[get_create_data_product_use_case] = lambda: mock_uc
    app.dependency_overrides[get_github_client] = lambda: mock_github
    app.dependency_overrides[get_data_contract_repository] = lambda: mock_contract_repo
    app.dependency_overrides[get_data_product_repository] = lambda: mock_product_repo

    resp = admin_client.post(
        "/api/v1/data-products",
        json={
            "name": "Attribution Model",
            "description": "desc",
            "data_contracts_id": str(CONTRACT_ID),
        },
    )
    assert resp.status_code == 201
    mock_github.create_product_repo.assert_awaited_once()
    args, kwargs = mock_github.create_product_repo.await_args
    assert args[0] == "dp-marketing-attribution-model"
    mock_github.push_scaffold.assert_awaited_once()
    mock_product_repo.update_repo_url.assert_awaited_once()
    assert (
        resp.json()["repo_url"]
        == "https://github.com/acme/dp-marketing-attribution-model"
    )


def test_create_data_product_warns_when_github_unavailable(admin_client):
    mock_uc = AsyncMock()
    mock_uc.execute.return_value = _product()
    app.dependency_overrides[get_create_data_product_use_case] = lambda: mock_uc
    app.dependency_overrides[get_github_client] = lambda: None
    app.dependency_overrides[get_data_contract_repository] = lambda: AsyncMock()
    app.dependency_overrides[get_data_product_repository] = lambda: AsyncMock()
    resp = admin_client.post(
        "/api/v1/data-products",
        json={
            "name": "X",
            "description": "y",
            "data_contracts_id": str(CONTRACT_ID),
        },
    )
    assert resp.status_code == 201
    assert resp.json()["repo_url"] is None


def test_create_data_product_swallows_github_errors(admin_client):
    mock_uc = AsyncMock()
    mock_uc.execute.return_value = _product()
    mock_github = AsyncMock()
    mock_github.create_product_repo.side_effect = RuntimeError("boom")
    mock_contract_repo = AsyncMock()
    mock_contract_repo.get_by_id.return_value = _StubContract("Marketing")
    mock_product_repo = AsyncMock()
    app.dependency_overrides[get_create_data_product_use_case] = lambda: mock_uc
    app.dependency_overrides[get_github_client] = lambda: mock_github
    app.dependency_overrides[get_data_contract_repository] = lambda: mock_contract_repo
    app.dependency_overrides[get_data_product_repository] = lambda: mock_product_repo
    resp = admin_client.post(
        "/api/v1/data-products",
        json={"name": "X", "description": "y", "data_contracts_id": str(CONTRACT_ID)},
    )
    assert resp.status_code == 201
    assert resp.json()["repo_url"] is None
    mock_product_repo.update_repo_url.assert_not_awaited()
