from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.infra.config import CORS_ORIGINS
from backend.interface.routers import api_router

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)
