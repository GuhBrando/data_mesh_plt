import uuid
from typing import Any, List

import yaml
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import PlainTextResponse

from backend.domain.entities.contract_stakeholder import ContractStakeholder
from backend.domain.entities.data_contract import DataContract
from backend.domain.entities.user import User
from backend.domain.value_objects.user_role import UserRole
from backend.infra.postgres import get_db_connection
from backend.interface.dependencies import (
    get_assign_stakeholder_use_case,
    get_create_data_contract_use_case,
    get_delete_data_contract_use_case,
    get_get_data_contract_use_case,
    get_list_data_contracts_use_case,
    get_remove_stakeholder_use_case,
    get_stakeholder_repository,
    get_update_data_contract_use_case,
)
from backend.interface.permissions import is_domain_member, require_roles
from backend.interface.schemas.data_contract import (
    DataContractCreateModel,
    DataContractResponseModel,
    DataContractUpdateModel,
)
from backend.interface.schemas.stakeholder import (
    StakeholderAssignModel,
    StakeholderResponseModel,
)
from backend.interface.security import get_current_user
from backend.use_cases.data_contract.create import CreateDataContractUseCase
from backend.use_cases.data_contract.delete import DeleteDataContractUseCase
from backend.use_cases.data_contract.get import GetDataContractUseCase
from backend.use_cases.data_contract.list import ListDataContractsUseCase
from backend.use_cases.data_contract.update import UpdateDataContractUseCase
from backend.use_cases.stakeholder.assign import AssignStakeholderUseCase
from backend.use_cases.stakeholder.remove import RemoveStakeholderUseCase

router = APIRouter()

_steward_or_admin = require_roles(UserRole.PLATFORM_ADMIN, UserRole.DATA_STEWARD)
_owner_or_admin = require_roles(UserRole.PLATFORM_ADMIN, UserRole.DATA_OWNER)


def _to_response(contract: DataContract) -> DataContractResponseModel:
    return DataContractResponseModel(
        id=contract.id,
        title=contract.title,
        version=contract.version,
        owner=contract.owner,
        domain=contract.domain,
        tier=contract.tier,
        status=contract.status,
        models=contract.models,
        servicelevels=contract.servicelevels,
        domain_id=contract.domain_id,
        created_at=contract.created_at,
        updated_at=contract.updated_at,
    )


def _stakeholder_to_response(s: ContractStakeholder) -> StakeholderResponseModel:
    return StakeholderResponseModel(
        contract_id=s.contract_id,
        user_id=s.user_id,
        assigned_by=s.assigned_by,
        assigned_at=s.assigned_at,
    )


def _assemble_yaml(contract: DataContract) -> str:
    models_data = dict(contract.models)
    quality_data = models_data.pop("quality", [])
    payload: dict[str, Any] = {
        "dataContractSpecification": "0.9.3",
        "id": str(contract.id),
        "info": {
            "title": contract.title,
            "version": contract.version,
            "owner": contract.owner,
            "domain": contract.domain,
            "status": contract.status,
        },
        "models": models_data,
        "servicelevels": contract.servicelevels,
        "x-tier": contract.tier,
    }
    if quality_data:
        payload["quality"] = quality_data
    return yaml.dump(
        payload, default_flow_style=False, allow_unicode=True, sort_keys=False
    )


@router.post(
    "/data-contracts", response_model=DataContractResponseModel, status_code=201
)
async def create_data_contract(
    body: DataContractCreateModel,
    use_case: CreateDataContractUseCase = Depends(get_create_data_contract_use_case),
    current_user: User = Depends(_steward_or_admin),
    db=Depends(get_db_connection),
):
    if (
        current_user.role == UserRole.DATA_STEWARD
        and body.domain_id
        and not await is_domain_member(current_user.id, body.domain_id, db)
    ):
        raise HTTPException(status_code=403, detail="Not a member of this domain")
    try:
        contract = await use_case.execute(
            title=body.title,
            version=body.version,
            owner=body.owner,
            domain=body.domain,
            tier=body.tier,
            status=body.status,
            models=body.models.model_dump(),
            servicelevels=body.servicelevels.model_dump(),
            domain_id=body.domain_id,
        )
        return _to_response(contract)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/data-contracts", response_model=List[DataContractResponseModel])
async def list_data_contracts(
    use_case: ListDataContractsUseCase = Depends(get_list_data_contracts_use_case),
    _: User = Depends(get_current_user),
):
    contracts = await use_case.execute()
    return [_to_response(c) for c in contracts]


@router.get("/data-contracts/{contract_id}/yaml", response_class=PlainTextResponse)
async def get_data_contract_yaml(
    contract_id: uuid.UUID,
    use_case: GetDataContractUseCase = Depends(get_get_data_contract_use_case),
    _: User = Depends(get_current_user),
):
    contract = await use_case.execute(contract_id)
    if not contract:
        raise HTTPException(status_code=404, detail="Data contract not found")
    return PlainTextResponse(_assemble_yaml(contract), media_type="text/plain")


@router.get("/data-contracts/{contract_id}", response_model=DataContractResponseModel)
async def get_data_contract(
    contract_id: uuid.UUID,
    use_case: GetDataContractUseCase = Depends(get_get_data_contract_use_case),
    stakeholder_repo=Depends(get_stakeholder_repository),
    current_user: User = Depends(get_current_user),
):
    is_consumer = current_user.role == UserRole.DATA_CONSUMER
    is_stakeholder = await stakeholder_repo.is_stakeholder(contract_id, current_user.id)
    if is_consumer and not is_stakeholder:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    contract = await use_case.execute(contract_id)
    if not contract:
        raise HTTPException(status_code=404, detail="Data contract not found")
    return _to_response(contract)


@router.put("/data-contracts/{contract_id}", response_model=DataContractResponseModel)
async def update_data_contract(
    contract_id: uuid.UUID,
    body: DataContractUpdateModel,
    use_case: UpdateDataContractUseCase = Depends(get_update_data_contract_use_case),
    get_use_case: GetDataContractUseCase = Depends(get_get_data_contract_use_case),
    current_user: User = Depends(_steward_or_admin),
    db=Depends(get_db_connection),
):
    existing = await get_use_case.execute(contract_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Data contract not found")
    if (
        current_user.role == UserRole.DATA_STEWARD
        and existing.domain_id
        and not await is_domain_member(current_user.id, existing.domain_id, db)
    ):
        raise HTTPException(status_code=403, detail="Not a member of this domain")
    try:
        contract = await use_case.execute(
            contract_id=contract_id,
            title=body.title if body.title is not None else existing.title,
            version=body.version if body.version is not None else existing.version,
            owner=body.owner if body.owner is not None else existing.owner,
            domain=body.domain if body.domain is not None else existing.domain,
            tier=body.tier if body.tier is not None else existing.tier,
            status=body.status if body.status is not None else existing.status,
            models=body.models.model_dump()
            if body.models is not None
            else existing.models,
            servicelevels=(
                body.servicelevels.model_dump()
                if body.servicelevels is not None
                else existing.servicelevels
            ),
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    if not contract:
        raise HTTPException(status_code=404, detail="Data contract not found")
    return _to_response(contract)


@router.delete("/data-contracts/{contract_id}", status_code=204)
async def delete_data_contract(
    contract_id: uuid.UUID,
    use_case: DeleteDataContractUseCase = Depends(get_delete_data_contract_use_case),
    get_use_case: GetDataContractUseCase = Depends(get_get_data_contract_use_case),
    current_user: User = Depends(_owner_or_admin),
    db=Depends(get_db_connection),
):
    if current_user.role == UserRole.DATA_OWNER:
        contract = await get_use_case.execute(contract_id)
        if not contract:
            raise HTTPException(status_code=404, detail="Data contract not found")
        if contract.domain_id and not await is_domain_member(
            current_user.id, contract.domain_id, db
        ):
            raise HTTPException(status_code=403, detail="Not a member of this domain")
    deleted = await use_case.execute(contract_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Data contract not found")


@router.post(
    "/data-contracts/{contract_id}/stakeholders",
    response_model=StakeholderResponseModel,
    status_code=201,
)
async def assign_stakeholder(
    contract_id: uuid.UUID,
    body: StakeholderAssignModel,
    use_case: AssignStakeholderUseCase = Depends(get_assign_stakeholder_use_case),
    get_use_case: GetDataContractUseCase = Depends(get_get_data_contract_use_case),
    current_user: User = Depends(_steward_or_admin),
    db=Depends(get_db_connection),
):
    if current_user.role == UserRole.DATA_STEWARD:
        contract = await get_use_case.execute(contract_id)
        if not contract:
            raise HTTPException(status_code=404, detail="Data contract not found")
        if contract.domain_id and not await is_domain_member(
            current_user.id, contract.domain_id, db
        ):
            raise HTTPException(status_code=403, detail="Not a member of this domain")
    stakeholder = await use_case.execute(
        contract_id=contract_id, user_id=body.user_id, assigned_by=current_user.id
    )
    return _stakeholder_to_response(stakeholder)


@router.delete("/data-contracts/{contract_id}/stakeholders/{user_id}", status_code=204)
async def remove_stakeholder(
    contract_id: uuid.UUID,
    user_id: uuid.UUID,
    use_case: RemoveStakeholderUseCase = Depends(get_remove_stakeholder_use_case),
    get_use_case: GetDataContractUseCase = Depends(get_get_data_contract_use_case),
    current_user: User = Depends(_steward_or_admin),
    db=Depends(get_db_connection),
):
    if current_user.role == UserRole.DATA_STEWARD:
        contract = await get_use_case.execute(contract_id)
        if not contract:
            raise HTTPException(status_code=404, detail="Data contract not found")
        if contract.domain_id and not await is_domain_member(
            current_user.id, contract.domain_id, db
        ):
            raise HTTPException(status_code=403, detail="Not a member of this domain")
    await use_case.execute(contract_id=contract_id, user_id=user_id)
