import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException

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
        obj=contract.obj,
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
        contract = await use_case.execute(obj=body.obj, domain_id=body.domain_id)
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


@router.get("/data-contracts/{contract_id}", response_model=DataContractResponseModel)
async def get_data_contract(
    contract_id: uuid.UUID,
    use_case: GetDataContractUseCase = Depends(get_get_data_contract_use_case),
    stakeholder_repo=Depends(get_stakeholder_repository),
    current_user: User = Depends(get_current_user),
):
    contract = await use_case.execute(contract_id)
    if not contract:
        raise HTTPException(status_code=404, detail="Data contract not found")
    is_stakeholder = await stakeholder_repo.is_stakeholder(contract_id, current_user.id)
    if current_user.role == UserRole.DATA_CONSUMER and not is_stakeholder:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
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
    if current_user.role == UserRole.DATA_STEWARD:
        contract = await get_use_case.execute(contract_id)
        if not contract:
            raise HTTPException(status_code=404, detail="Data contract not found")
        if contract.domain_id and not await is_domain_member(
            current_user.id, contract.domain_id, db
        ):
            raise HTTPException(status_code=403, detail="Not a member of this domain")
    try:
        contract = await use_case.execute(contract_id=contract_id, obj=body.obj)
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
