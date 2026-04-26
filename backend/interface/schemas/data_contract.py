import uuid
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class SchemaField(BaseModel):
    name: str
    type: Literal["string", "integer", "float", "boolean", "date", "timestamp"]
    description: str = ""
    nullable: bool = True
    primary_key: bool = False


class ModelsSection(BaseModel):
    fields: list[SchemaField] = []


class ServiceLevels(BaseModel):
    freshness: str = ""
    availability: str = ""
    retention: str = ""
    latency: str = ""


class DataContractCreateModel(BaseModel):
    title: str
    version: str = "1.0.0"
    owner: str
    domain: str
    tier: int = Field(..., ge=1, le=4)
    status: Literal["draft", "in_review", "active", "deprecated"] = "draft"
    models: ModelsSection = Field(default_factory=ModelsSection)
    servicelevels: ServiceLevels = Field(default_factory=ServiceLevels)


class DataContractUpdateModel(BaseModel):
    title: str | None = None
    version: str | None = None
    owner: str | None = None
    domain: str | None = None
    tier: int | None = Field(default=None, ge=1, le=4)
    status: Literal["draft", "in_review", "active", "deprecated"] | None = None
    models: ModelsSection | None = None
    servicelevels: ServiceLevels | None = None


class DataContractResponseModel(BaseModel):
    id: uuid.UUID
    title: str
    version: str
    owner: str
    domain: str
    tier: int
    status: str
    models: dict[str, Any]
    servicelevels: dict[str, Any]
    created_at: datetime
    updated_at: datetime
