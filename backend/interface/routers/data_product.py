import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException

from backend.domain.entities.data_product import DataProduct
from backend.interface.dependencies import (
    get_create_data_product_use_case,
    get_delete_data_product_use_case,
    get_get_data_product_use_case,
    get_list_data_products_use_case,
    get_update_data_product_use_case,
)
from backend.interface.schemas.data_product import (
    DataProductCreateModel,
    DataProductResponseModel,
    DataProductUpdateModel,
)
from backend.use_cases.data_product.create import CreateDataProductUseCase
from backend.use_cases.data_product.delete import DeleteDataProductUseCase
from backend.use_cases.data_product.get import GetDataProductUseCase
from backend.use_cases.data_product.list import ListDataProductsUseCase
from backend.use_cases.data_product.update import UpdateDataProductUseCase

router = APIRouter()


def _to_response(product: DataProduct) -> DataProductResponseModel:
    return DataProductResponseModel(
        id=product.id,
        name=product.name,
        description=product.description,
        data_contracts_id=product.data_contracts_id,
        created_at=product.created_at,
        updated_at=product.updated_at,
    )


@router.post("/data-products", response_model=DataProductResponseModel, status_code=201)
async def create_data_product(
    body: DataProductCreateModel,
    use_case: CreateDataProductUseCase = Depends(get_create_data_product_use_case),
):
    product = await use_case.execute(
        name=body.name,
        description=body.description,
        data_contracts_id=body.data_contracts_id,
    )
    return _to_response(product)


@router.get("/data-products", response_model=List[DataProductResponseModel])
async def list_data_products(
    use_case: ListDataProductsUseCase = Depends(get_list_data_products_use_case),
):
    products = await use_case.execute()
    return [_to_response(p) for p in products]


@router.get("/data-products/{product_id}", response_model=DataProductResponseModel)
async def get_data_product(
    product_id: uuid.UUID,
    use_case: GetDataProductUseCase = Depends(get_get_data_product_use_case),
):
    product = await use_case.execute(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Data product not found")
    return _to_response(product)


@router.put("/data-products/{product_id}", response_model=DataProductResponseModel)
async def update_data_product(
    product_id: uuid.UUID,
    body: DataProductUpdateModel,
    use_case: UpdateDataProductUseCase = Depends(get_update_data_product_use_case),
):
    product = await use_case.execute(
        product_id=product_id,
        name=body.name,
        description=body.description,
        data_contracts_id=body.data_contracts_id,
    )
    if not product:
        raise HTTPException(status_code=404, detail="Data product not found")
    return _to_response(product)


@router.delete("/data-products/{product_id}", status_code=204)
async def delete_data_product(
    product_id: uuid.UUID,
    use_case: DeleteDataProductUseCase = Depends(get_delete_data_product_use_case),
):
    deleted = await use_case.execute(product_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Data product not found")
