import uuid

from fastapi import APIRouter, Depends, HTTPException

from backend.domain.entities.domain import Domain
from backend.domain.entities.user import User
from backend.domain.value_objects.user_role import UserRole
from backend.infra.postgres import get_db_connection
from backend.interface.dependencies import (
    get_add_domain_member_use_case,
    get_create_domain_use_case,
    get_remove_domain_member_use_case,
)
from backend.interface.permissions import is_domain_member, require_roles
from backend.interface.schemas.domain import (
    DomainCreateModel,
    DomainMemberModel,
    DomainResponseModel,
)
from backend.use_cases.domain.add_member import AddDomainMemberUseCase
from backend.use_cases.domain.create import CreateDomainUseCase
from backend.use_cases.domain.remove_member import RemoveDomainMemberUseCase

router = APIRouter()

_admin_only = require_roles(UserRole.PLATFORM_ADMIN)
_admin_or_owner = require_roles(UserRole.PLATFORM_ADMIN, UserRole.DATA_OWNER)


def _to_response(domain: Domain) -> DomainResponseModel:
    return DomainResponseModel(id=domain.id, name=domain.name)


@router.post("/domains", response_model=DomainResponseModel, status_code=201)
async def create_domain(
    body: DomainCreateModel,
    use_case: CreateDomainUseCase = Depends(get_create_domain_use_case),
    _: User = Depends(_admin_only),
):
    domain = await use_case.execute(name=body.name)
    return _to_response(domain)


@router.post("/domains/{domain_id}/members", status_code=204)
async def add_domain_member(
    domain_id: uuid.UUID,
    body: DomainMemberModel,
    use_case: AddDomainMemberUseCase = Depends(get_add_domain_member_use_case),
    current_user: User = Depends(_admin_or_owner),
    db=Depends(get_db_connection),
):
    if current_user.role == UserRole.DATA_OWNER and not await is_domain_member(
        current_user.id, domain_id, db
    ):
        raise HTTPException(status_code=403, detail="Not a member of this domain")
    await use_case.execute(domain_id=domain_id, user_id=body.user_id)


@router.delete("/domains/{domain_id}/members/{user_id}", status_code=204)
async def remove_domain_member(
    domain_id: uuid.UUID,
    user_id: uuid.UUID,
    use_case: RemoveDomainMemberUseCase = Depends(get_remove_domain_member_use_case),
    current_user: User = Depends(_admin_or_owner),
    db=Depends(get_db_connection),
):
    if current_user.role == UserRole.DATA_OWNER and not await is_domain_member(
        current_user.id, domain_id, db
    ):
        raise HTTPException(status_code=403, detail="Not a member of this domain")
    await use_case.execute(domain_id=domain_id, user_id=user_id)
