import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException

from src.domain.entities.data_contract import DataContract
from src.interface.dependencies import (
    get_create_data_contract_use_case,
    get_delete_data_contract_use_case,
    get_get_data_contract_use_case,
    get_list_data_contracts_use_case,
    get_update_data_contract_use_case,
)
from src.interface.schemas.data_contract import (
    DataContractCreateModel,
    DataContractResponseModel,
    DataContractUpdateModel,
)
from src.use_cases.data_contract.create import CreateDataContractUseCase
from src.use_cases.data_contract.delete import DeleteDataContractUseCase
from src.use_cases.data_contract.get import GetDataContractUseCase
from src.use_cases.data_contract.list import ListDataContractsUseCase
from src.use_cases.data_contract.update import UpdateDataContractUseCase

router = APIRouter()


def _to_response(contract: DataContract) -> DataContractResponseModel:
    return DataContractResponseModel(
        id=contract.id,
        obj=contract.obj,
        created_at=contract.created_at,
        updated_at=contract.updated_at,
    )


@router.post(
    "/data-contracts", response_model=DataContractResponseModel, status_code=201
)
async def create_data_contract(
    body: DataContractCreateModel,
    use_case: CreateDataContractUseCase = Depends(get_create_data_contract_use_case),
):
    try:
        contract = await use_case.execute(obj=body.obj)
        return _to_response(contract)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/data-contracts", response_model=List[DataContractResponseModel])
async def list_data_contracts(
    use_case: ListDataContractsUseCase = Depends(get_list_data_contracts_use_case),
):
    contracts = await use_case.execute()
    return [_to_response(c) for c in contracts]


@router.get("/data-contracts/{contract_id}", response_model=DataContractResponseModel)
async def get_data_contract(
    contract_id: uuid.UUID,
    use_case: GetDataContractUseCase = Depends(get_get_data_contract_use_case),
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
):
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
):
    deleted = await use_case.execute(contract_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Data contract not found")
