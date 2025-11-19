"""
This module initializes the API router for the application.

It aggregates all the individual route modules and includes them in a single
APIRouter instance. Each route module is registered with its respective prefix
and tags to organize the API endpoints.

Routes:
- Example routes are included from the `data_contract` module.
"""

from fastapi import APIRouter

from src.interface.routers.data_contract import router as example_router

api_router = APIRouter()

api_router.include_router(example_router, prefix="/api/v1", tags=["Example"])
