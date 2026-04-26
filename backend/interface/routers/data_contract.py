import uuid
from typing import List

import yaml
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import PlainTextResponse

from backend.domain.entities.data_contract import DataContract
from backend.domain.entities.user import User
from backend.interface.dependencies import (
    get_create_data_contract_use_case,
    get_delete_data_contract_use_case,
    get_get_data_contract_use_case,
    get_list_data_contracts_use_case,
    get_update_data_contract_use_case,
)
from backend.interface.schemas.data_contract import (
    DataContractCreateModel,
    DataContractResponseModel,
    DataContractUpdateModel,
)
from backend.interface.security import get_current_user
from backend.use_cases.data_contract.create import CreateDataContractUseCase
from backend.use_cases.data_contract.delete import DeleteDataContractUseCase
from backend.use_cases.data_contract.get import GetDataContractUseCase
from backend.use_cases.data_contract.list import ListDataContractsUseCase
from backend.use_cases.data_contract.update import UpdateDataContractUseCase

router = APIRouter()


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
        created_at=contract.created_at,
        updated_at=contract.updated_at,
    )


def _assemble_yaml(contract: DataContract) -> str:
    payload = {
        "dataContractSpecification": "0.9.3",
        "id": str(contract.id),
        "info": {
            "title": contract.title,
            "version": contract.version,
            "owner": contract.owner,
            "domain": contract.domain,
            "status": contract.status,
        },
        "models": contract.models,
        "servicelevels": contract.servicelevels,
        "x-tier": contract.tier,
    }
    return yaml.dump(
        payload, default_flow_style=False, allow_unicode=True, sort_keys=False
    )


@router.post(
    "/data-contracts", response_model=DataContractResponseModel, status_code=201
)
async def create_data_contract(
    body: DataContractCreateModel,
    use_case: CreateDataContractUseCase = Depends(get_create_data_contract_use_case),
    _: User = Depends(get_current_user),
):
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
    _: User = Depends(get_current_user),
):
    contract = await use_case.execute(contract_id)
    if not contract:
        raise HTTPException(status_code=404, detail="Data contract not found")
    return _to_response(contract)


@router.put("/data-contracts/{contract_id}", response_model=DataContractResponseModel)
async def update_data_contract(
    contract_id: uuid.UUID,
    body: DataContractUpdateModel,
    use_case: UpdateDataContractUseCase = Depends(get_update_data_contract_use_case),
    _: User = Depends(get_current_user),
):
    existing = await GetDataContractUseCase(use_case.repository).execute(contract_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Data contract not found")

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
            servicelevels=body.servicelevels.model_dump()
            if body.servicelevels is not None
            else existing.servicelevels,
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
    _: User = Depends(get_current_user),
):
    deleted = await use_case.execute(contract_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Data contract not found")
