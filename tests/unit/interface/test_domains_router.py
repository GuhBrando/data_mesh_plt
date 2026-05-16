import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient

from backend.domain.entities.domain import Domain, DomainMember
from backend.domain.entities.user import User
from backend.domain.value_objects.email import Email
from backend.domain.value_objects.user_role import UserRole
from backend.infra.postgres import get_db_connection
from backend.interface.dependencies import (
    get_add_domain_member_use_case,
    get_create_domain_use_case,
    get_data_contract_repository,
    get_delete_domain_use_case,
    get_github_client,
    get_list_domains_use_case,
    get_remove_domain_member_use_case,
    get_update_domain_member_use_case,
    get_update_domain_use_case,
)
from backend.interface.security import get_current_user
from backend.main import app

NOW = datetime.now(tz=timezone.utc)
DOMAIN_ID = uuid.uuid4()
USER_ID = uuid.uuid4()


def _domain(**kw) -> Domain:
    return Domain(
        id=kw.get("id", DOMAIN_ID),
        name=kw.get("name", "Commerce"),
        description=kw.get("description", ""),
        owner_id=kw.get("owner_id", None),
        owner_username=kw.get("owner_username", ""),
        members=kw.get("members", []),
        contract_count=kw.get("contract_count", 0),
        created_at=NOW,
        updated_at=NOW,
    )


def _member() -> DomainMember:
    return DomainMember(user_id=USER_ID, username="alice", role="member")


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
    app.dependency_overrides[get_github_client] = lambda: None
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_list_domains(admin_client):
    mock_uc = AsyncMock()
    mock_uc.execute.return_value = [_domain()]
    app.dependency_overrides[get_list_domains_use_case] = lambda: mock_uc
    resp = admin_client.get("/api/v1/domains")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["name"] == "Commerce"


def test_list_domains_empty(admin_client):
    mock_uc = AsyncMock()
    mock_uc.execute.return_value = []
    app.dependency_overrides[get_list_domains_use_case] = lambda: mock_uc
    resp = admin_client.get("/api/v1/domains")
    assert resp.status_code == 200
    assert resp.json() == []


def test_create_domain(admin_client):
    mock_uc = AsyncMock()
    mock_uc.execute.return_value = _domain(name="Finance")
    app.dependency_overrides[get_create_domain_use_case] = lambda: mock_uc
    resp = admin_client.post("/api/v1/domains", json={"name": "Finance"})
    assert resp.status_code == 201
    assert resp.json()["name"] == "Finance"


def test_create_domain_with_owner(admin_client):
    mock_uc = AsyncMock()
    mock_uc.execute.return_value = _domain(name="Ops", owner_id=USER_ID)
    app.dependency_overrides[get_create_domain_use_case] = lambda: mock_uc
    resp = admin_client.post(
        "/api/v1/domains",
        json={"name": "Ops", "description": "Operations", "owner_id": str(USER_ID)},
    )
    assert resp.status_code == 201


def test_update_domain(admin_client):
    existing = _domain(name="Old")
    updated = _domain(name="New")
    mock_uc = MagicMock()
    mock_uc.repository.get_by_id = AsyncMock(return_value=existing)
    mock_uc.execute = AsyncMock(return_value=updated)
    app.dependency_overrides[get_update_domain_use_case] = lambda: mock_uc
    app.dependency_overrides[get_data_contract_repository] = lambda: AsyncMock()
    resp = admin_client.put(f"/api/v1/domains/{DOMAIN_ID}", json={"name": "New"})
    assert resp.status_code == 200
    assert resp.json()["name"] == "New"


def test_update_domain_not_found(admin_client):
    mock_uc = MagicMock()
    mock_uc.repository.get_by_id = AsyncMock(return_value=None)
    app.dependency_overrides[get_update_domain_use_case] = lambda: mock_uc
    app.dependency_overrides[get_data_contract_repository] = lambda: AsyncMock()
    resp = admin_client.put(f"/api/v1/domains/{uuid.uuid4()}", json={"name": "X"})
    assert resp.status_code == 404


def test_update_domain_execute_returns_none(admin_client):
    existing = _domain(name="Old")
    mock_uc = MagicMock()
    mock_uc.repository.get_by_id = AsyncMock(return_value=existing)
    mock_uc.execute = AsyncMock(return_value=None)
    app.dependency_overrides[get_update_domain_use_case] = lambda: mock_uc
    app.dependency_overrides[get_data_contract_repository] = lambda: AsyncMock()
    resp = admin_client.put(f"/api/v1/domains/{DOMAIN_ID}", json={"name": "X"})
    assert resp.status_code == 404


def test_delete_domain(admin_client):
    mock_uc = AsyncMock()
    mock_uc.execute.return_value = True
    app.dependency_overrides[get_delete_domain_use_case] = lambda: mock_uc
    resp = admin_client.delete(f"/api/v1/domains/{DOMAIN_ID}")
    assert resp.status_code == 204


def test_delete_domain_not_found(admin_client):
    mock_uc = AsyncMock()
    mock_uc.execute.return_value = False
    app.dependency_overrides[get_delete_domain_use_case] = lambda: mock_uc
    resp = admin_client.delete(f"/api/v1/domains/{uuid.uuid4()}")
    assert resp.status_code == 404


def test_delete_domain_conflict(admin_client):
    mock_uc = AsyncMock()
    mock_uc.execute.side_effect = ValueError("Has contracts")
    app.dependency_overrides[get_delete_domain_use_case] = lambda: mock_uc
    resp = admin_client.delete(f"/api/v1/domains/{DOMAIN_ID}")
    assert resp.status_code == 409


def test_add_domain_member(admin_client):
    mock_uc = AsyncMock()
    mock_uc.execute.return_value = _member()
    app.dependency_overrides[get_add_domain_member_use_case] = lambda: mock_uc
    resp = admin_client.post(
        f"/api/v1/domains/{DOMAIN_ID}/members",
        json={"user_id": str(USER_ID), "role": "member"},
    )
    assert resp.status_code == 201
    assert resp.json()["role"] == "member"


def test_update_domain_member(admin_client):
    mock_uc = AsyncMock()
    mock_uc.execute.return_value = _member()
    app.dependency_overrides[get_update_domain_member_use_case] = lambda: mock_uc
    resp = admin_client.patch(
        f"/api/v1/domains/{DOMAIN_ID}/members/{USER_ID}",
        json={"role": "maintainer"},
    )
    assert resp.status_code == 200
    assert resp.json()["username"] == "alice"


def test_remove_domain_member(admin_client):
    mock_uc = AsyncMock()
    mock_uc.execute.return_value = None
    app.dependency_overrides[get_remove_domain_member_use_case] = lambda: mock_uc
    resp = admin_client.delete(f"/api/v1/domains/{DOMAIN_ID}/members/{USER_ID}")
    assert resp.status_code == 204
