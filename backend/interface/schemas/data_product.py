import uuid
from datetime import datetime

from pydantic import BaseModel


class DataProductCreateModel(BaseModel):
    name: str
    description: str
    data_contracts_id: uuid.UUID


class DataProductResponseModel(BaseModel):
    id: uuid.UUID
    name: str
    description: str
    data_contracts_id: uuid.UUID
    created_at: datetime
    updated_at: datetime


class DataProductUpdateModel(BaseModel):
    name: str | None = None
    description: str | None = None
    data_contracts_id: uuid.UUID | None = None
