from fastapi import APIRouter

from backend.interface.routers.auth import router as auth_router
from backend.interface.routers.data_contract import router as data_contract_router
from backend.interface.routers.data_product import router as data_product_router
from backend.interface.routers.domains import router as domains_router
from backend.interface.routers.users import router as users_router

api_router = APIRouter()

api_router.include_router(auth_router, prefix="/api/v1", tags=["Auth"])
api_router.include_router(users_router, prefix="/api/v1", tags=["Users"])
api_router.include_router(
    data_contract_router, prefix="/api/v1", tags=["Data Contracts"]
)
api_router.include_router(data_product_router, prefix="/api/v1", tags=["Data Products"])
api_router.include_router(domains_router, prefix="/api/v1", tags=["Domains"])
