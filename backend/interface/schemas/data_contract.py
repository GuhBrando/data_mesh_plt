import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel


class DataContractCreateModel(BaseModel):
    obj: dict[str, Any]


class DataContractResponseModel(BaseModel):
    id: uuid.UUID
    obj: dict[str, Any]
    created_at: datetime
    updated_at: datetime


class DataContractUpdateModel(BaseModel):
    obj: dict[str, Any]
