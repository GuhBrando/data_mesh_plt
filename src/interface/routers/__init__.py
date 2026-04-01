"""
This module initializes the API router for the application.

It aggregates all the individual route modules and includes them in a single
APIRouter instance. Each route module is registered with its respective prefix
and tags to organize the API endpoints.
"""

from fastapi import APIRouter

from src.interface.routers.data_contract import router as data_contract_router
from src.interface.routers.data_product import router as data_product_router
from src.interface.routers.users import router as users_router

api_router = APIRouter()

api_router.include_router(users_router, prefix="/api/v1", tags=["Users"])
api_router.include_router(
    data_contract_router, prefix="/api/v1", tags=["Data Contracts"]
)
api_router.include_router(data_product_router, prefix="/api/v1", tags=["Data Products"])
