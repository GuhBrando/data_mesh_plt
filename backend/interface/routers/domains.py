import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException

from backend.domain.entities.domain import Domain, DomainMember
from backend.domain.entities.user import User
from backend.domain.value_objects.user_role import UserRole
from backend.infra.postgres import get_db_connection
from backend.interface.dependencies import (
    get_add_domain_member_use_case,
    get_create_domain_use_case,
    get_delete_domain_use_case,
    get_list_domains_use_case,
    get_remove_domain_member_use_case,
    get_update_domain_member_use_case,
    get_update_domain_use_case,
)
from backend.interface.permissions import is_domain_member, require_roles
from backend.interface.schemas.domain import (
    DomainAddMemberModel,
    DomainCreateModel,
    DomainMemberResponse,
    DomainUpdateMemberModel,
    DomainUpdateModel,
    DomainWithMembersResponse,
)
from backend.interface.security import get_current_user
from backend.use_cases.domain.add_member import AddDomainMemberUseCase
from backend.use_cases.domain.create import CreateDomainUseCase
from backend.use_cases.domain.delete import DeleteDomainUseCase
from backend.use_cases.domain.list import ListDomainsUseCase
from backend.use_cases.domain.remove_member import RemoveDomainMemberUseCase
from backend.use_cases.domain.update import UpdateDomainUseCase
from backend.use_cases.domain.update_member import UpdateDomainMemberUseCase

router = APIRouter()

_admin_only = require_roles(UserRole.PLATFORM_ADMIN)
_admin_or_owner = require_roles(UserRole.PLATFORM_ADMIN, UserRole.DATA_OWNER)


def _domain_to_response(domain: Domain) -> DomainWithMembersResponse:
    return DomainWithMembersResponse(
        id=domain.id,
        name=domain.name,
        description=domain.description,
        owner_id=domain.owner_id,
        owner_username=domain.owner_username,
        members=[
            DomainMemberResponse(
                user_id=m.user_id,
                username=m.username,
                role=m.role,
            )
            for m in domain.members
        ],
        contract_count=domain.contract_count,
        created_at=domain.created_at,
        updated_at=domain.updated_at,
    )


def _member_to_response(member: DomainMember) -> DomainMemberResponse:
    return DomainMemberResponse(
        user_id=member.user_id,
        username=member.username,
        role=member.role,
    )


@router.get("/domains", response_model=List[DomainWithMembersResponse])
async def list_domains(
    use_case: ListDomainsUseCase = Depends(get_list_domains_use_case),
    _: User = Depends(get_current_user),
):
    domains = await use_case.execute()
    return [_domain_to_response(d) for d in domains]


@router.post("/domains", response_model=DomainWithMembersResponse, status_code=201)
async def create_domain(
    body: DomainCreateModel,
    use_case: CreateDomainUseCase = Depends(get_create_domain_use_case),
    _: User = Depends(_admin_only),
):
    domain = await use_case.execute(
        name=body.name,
        description=body.description,
        owner_id=body.owner_id,
    )
    return _domain_to_response(domain)


@router.put("/domains/{domain_id}", response_model=DomainWithMembersResponse)
async def update_domain(
    domain_id: uuid.UUID,
    body: DomainUpdateModel,
    use_case: UpdateDomainUseCase = Depends(get_update_domain_use_case),
    current_user: User = Depends(get_current_user),
    db=Depends(get_db_connection),
):
    # Allow PLATFORM_ADMIN or the domain's owner
    if current_user.role != UserRole.PLATFORM_ADMIN:
        from backend.infra.repositories.domain_repository import (
            PostgresDomainRepository,
        )

        repo = PostgresDomainRepository(db)
        existing = await repo.get_by_id(domain_id)
        if not existing or existing.owner_id != current_user.id:
            raise HTTPException(status_code=403, detail="Forbidden")

    domain = await use_case.execute(
        domain_id=domain_id,
        name=body.name,
        description=body.description,
        owner_id=body.owner_id,
    )
    if not domain:
        raise HTTPException(status_code=404, detail="Domain not found")
    return _domain_to_response(domain)


@router.delete("/domains/{domain_id}", status_code=204)
async def delete_domain(
    domain_id: uuid.UUID,
    use_case: DeleteDomainUseCase = Depends(get_delete_domain_use_case),
    _: User = Depends(_admin_only),
):
    deleted = await use_case.execute(domain_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Domain not found")


@router.post(
    "/domains/{domain_id}/members",
    response_model=DomainMemberResponse,
    status_code=201,
)
async def add_domain_member(
    domain_id: uuid.UUID,
    body: DomainAddMemberModel,
    use_case: AddDomainMemberUseCase = Depends(get_add_domain_member_use_case),
    current_user: User = Depends(_admin_or_owner),
    db=Depends(get_db_connection),
):
    if current_user.role == UserRole.DATA_OWNER and not await is_domain_member(
        current_user.id, domain_id, db
    ):
        raise HTTPException(status_code=403, detail="Not a member of this domain")
    member = await use_case.execute(
        domain_id=domain_id,
        user_id=body.user_id,
        role=body.role,
    )
    return _member_to_response(member)


@router.patch(
    "/domains/{domain_id}/members/{user_id}", response_model=DomainMemberResponse
)
async def update_domain_member(
    domain_id: uuid.UUID,
    user_id: uuid.UUID,
    body: DomainUpdateMemberModel,
    use_case: UpdateDomainMemberUseCase = Depends(get_update_domain_member_use_case),
    current_user: User = Depends(_admin_or_owner),
    db=Depends(get_db_connection),
):
    if current_user.role == UserRole.DATA_OWNER and not await is_domain_member(
        current_user.id, domain_id, db
    ):
        raise HTTPException(status_code=403, detail="Not a member of this domain")
    member = await use_case.execute(
        domain_id=domain_id,
        user_id=user_id,
        role=body.role,
    )
    return _member_to_response(member)


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
